from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
from src.driver_singleton import Driver
from typing import Dict
Base = declarative_base()

treasury_address = "13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB"


class Transaction(GraphObject):
    extrinsic_hash = Property()
    amount_transferred = Property()
    has_extrinsic_function = RelatedTo("ExtrinsicFunction")
    has_event_function = RelatedTo("EventFunction")

    from_balance = RelatedTo("Balance")
    to_balance = RelatedTo("Balance")
    reward_validator = RelatedTo("Balance")
    reward_treasury = RelatedTo("Balance")

    @staticmethod
    def create(block: Block, transaction_data, event_data) -> "Transaction":
        # transaction failed so we don't include it
        if event_data[-1]["event_id"] != "ExtrinsicSuccess":
            return None

        transaction = Transaction(
            extrinsic_hash=transaction_data["extrinsic_hash"]
        )
        extrinsic_function = ExtrinsicFunction.get(transaction_data["call"]["call_function"])
        if not extrinsic_function:
            extrinsic_function = ExtrinsicFunction.create(transaction_data["call"]["call_function"],
                                                          transaction_data["call"]["call_module"])

        transaction.has_extrinsic_function.add(extrinsic_function)

        if extrinsic_function.name in ["transfer", "transfer_all", "transfer_keep_alive"]:
            Transaction.handle_transfer(transaction_data, event_data, block, transaction)

        elif extrinsic_function.name in ["bond", "bond_extra"]:
            Transaction.handle_bond(transaction_data, event_data, block, transaction, extrinsic_function)

        elif extrinsic_function.name == "set_controller":
            from_account = Account.get(transaction_data["address"].replace("0x", ""))
            if not from_account:
                from_account = Account.create(transaction_data["address"].replace("0x", ""))

            balance = Account.get_current_balance(from_account)

            controller_address = transaction_data["call"]["call_args"][0]["value"].replace("0x", "")

            controller_account = Account.get(controller_address)
            if not controller_account:
                controller_account = Account.create(controller_address)
            controller_account.controls.add(from_account)
            Account.save(controller_account)

            amount_transferred = 0

            transaction.amount_transferred = amount_transferred
            fee = Transaction.pay_fees(event_data, block, transaction)

            from_account.update_balance(block.block_number, from_account, transferable=-(amount_transferred + fee),
                                        bonded=amount_transferred)

            transaction.from_balance.add(from_account.get_current_balance())
            transaction.to_balance.add(from_account.get_current_balance())
        elif extrinsic_function.name == "set_payee":
            Transaction.handle_set_payee(transaction_data, event_data, block, transaction, extrinsic_function)

        Transaction.save(transaction)
        block.has_transaction.add(transaction)
        Block.save(block)
        return transaction

    @staticmethod
    def save(transaction: "Transaction"):
        Driver().get_driver().save(transaction)

    @staticmethod
    def handle_transfer(transaction_data: Dict, event_data: Dict, block: Block, transaction: "Transaction"):
        from_account = Account.get(transaction_data["address"].replace("0x", ""))
        if not from_account:
            from_account = Account.create(transaction_data["address"].replace("0x", ""))
        to_account = Account.get(transaction_data["call"]["call_args"][0]["value"].replace("0x", ""))

        if not to_account:
            to_account = Account.create(transaction_data["call"]["call_args"][0]["value"].replace("0x", ""))

        fee = Transaction.pay_fees(event_data, block, transaction)

        for event in event_data:
            if event['event_id'] == 'Transfer':
                amount_transferred = event['attributes'][2]['value']

        transaction.amount_transferred = amount_transferred

        from_account.update_balance(block.block_number, to_account, transferable=-(amount_transferred + fee))
        to_account.update_balance(transferable=amount_transferred)

        transaction.from_balance.add(from_account.get_current_balance())
        transaction.to_balance.add(to_account.get_current_balance())

    @staticmethod
    def handle_bond(transaction_data: Dict, event_data: Dict, block: Block, transaction: "Transaction",
                    extrinsic_function: "ExtrinsicFunction"):
        from_account = Account.get(transaction_data["address"].replace("0x", ""))
        if not from_account:
            from_account = Account.create(transaction_data["address"].replace("0x", ""))
        balance = Account.get_current_balance(from_account)

        if extrinsic_function.name == "bond":
            amount_transferred = transaction_data["call"]["call_args"][1]["value"]
            controller_address = transaction_data["call"]["call_args"][0]["value"].replace("0x", "")
            reward_destination = transaction_data["call"]["call_args"][2]["value"]
            controller_account = Account.get(controller_address)
            if not controller_account:
                controller_account = Account.create(controller_address)
            controller_account.controls.add(from_account)
            controller_account.reward_destination = reward_destination

            Account.save(controller_account)
        elif extrinsic_function.name == "bond_extra":
            amount_transferred = transaction_data["call"]["call_args"][0]["value"]
        else:
            raise NotImplementedError()

        transaction.amount_transferred = amount_transferred
        fee = Transaction.pay_fees(event_data, block, transaction)
        from_account = Account.get(transaction_data["address"].replace("0x", ""))  # have to get account again in case
        # controller is the same as from account, else everything updated gets overwritten in update balance.
        from_account.update_balance(block.block_number, from_account, transferable=-(amount_transferred + fee),
                                    bonded=amount_transferred)
        transaction.from_balance.add(from_account.get_current_balance())
        transaction.to_balance.add(from_account.get_current_balance())

    @staticmethod
    def pay_fees(event_data, block, transaction):
        validator_node = list(block.has_author.triples())[0][-1]
        validator_account = list(validator_node.account.triples())[0][-1]
        treasury_account = Account.get_treasury()
        try:
            validator_fee = event_data[-2]["attributes"][1]["value"]
            treasury_fee = event_data[-3]["attributes"][0]["value"]
            treasury_account.update_balance(transferable=treasury_fee)
            transaction.reward_treasury.add(treasury_account.get_current_balance())
        except IndexError:
            validator_fee = event_data[-2]["attributes"][1]["value"]
            treasury_fee = 0

        validator_account.update_balance(transferable=validator_fee)

        transaction.reward_validator.add(validator_account.get_current_balance())

        return (validator_fee + treasury_fee)

    @staticmethod
    def handle_set_payee(transaction_data, event_data, block, transaction, extrinsic_function):
        account = Account.get(transaction_data['address'])
        if not account:
            raise Exception("This should not have happened")
        reward_destination = transaction_data['call']['call_args'][0]['value']
        account.reward_destination = reward_destination
        Account.save(account)