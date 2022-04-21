from sqlalchemy import select
from src.pg_models import Account, Balance
from copy import deepcopy

class AbstractEventHandler:
    def __init__(self, session):
        self.session=session


    def get_account(self, address):
        stmt = select(Account).where(Account.address == address)
        account = self.session.execute(stmt).fetchone()
        if account is None:
            return account
        else:
            return account[0]
        

    def create_account(self, address, account_index=None, nonce=None, role=None,commit=True) -> Account:
        account = Account(
            address=address,
            account_index=None,
            nonce=None,
            role=None
        )
        if commit:
            self.session.add(account)
            self.session.commit()
        return account
    
    def get_or_create_account(self, address, account_index=None, nonce=None, role=None,commit=True):
        account = self.get_account(address)
        if account is None:
            account = self.create_account(address, account_index, nonce, role, commit)
        return account

    def get_last_balance(self, account: Account) -> Balance:
        stmt = select(Balance).where(Balance.account == account.address)
        balances = self.session.execute(stmt).fetchall()
        if len(balances) == 0:
            return None
        balance = deepcopy(balances[-1])[0]
        return balance

    def create_empty_balance(self, address, block_number, commit=True) -> Balance:
            balance = Balance(
                transferable=0,
                reserved=0,
                bonded=0,
                unbonding=0,
                block_number=block_number,
                account=address
            )
            if commit:
                self.session.add(balance)
                self.session.commit()
            return balance

    def get_or_create_last_balance(self, account, block_number, commit=True):
        balance = self.get_last_balance(account)
        if balance is None:
            balance = self.create_empty_balance(account.address, block_number, commit)
        
        return balance

    def create_transfer_in_balances(self,from_balance: Balance, to_balance: Balance, value: int, from_subbalance: str, to_subbalance: str):
        if from_balance.address == to_balance.address:
            return self.internal_transfer(from_balance, from_subbalance, to_subbalance, value)
        from_updated_value = getattr(from_balance, from_subbalance) - value
        setattr(from_balance, from_subbalance, from_updated_value)
        to_updated_value = getattr(to_balance, to_subbalance) + value
        setattr(to_balance, to_subbalance, to_updated_value)

        self.session.add(from_balance)
        self.session.add(to_balance)
        self.session.commit()

    def create_internal_transfer_in_balances(self,balance, from_subbalance, to_subbalance, value):

            updated_value = getattr(balance, from_subbalance) - value
            setattr(balance, from_subbalance, updated_value)
            to_updated_value = getattr(balance, to_subbalance) + value
            setattr(balance, to_subbalance, to_updated_value)

            self.session.add(balance)
            self.session.commit()
