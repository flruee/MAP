import logging
from typing import List
import datetime
import json

from src.pg_models.validator_config import ValidatorConfig
from .driver_singleton import Driver
from src.pg_models.aggregator import Aggregator
from src.pg_models.validator_pool import ValidatorPool
from src.pg_models.balance import Balance
from src.event_handlers.utils import event_error_handling
#from src.pg_models import Block as b,Extrinsic as e,Event as v
from src.pg_models.block import Block
from src.pg_models.extrinsic import Extrinsic
from src.pg_models.event import Event
from src.pg_models.account import Account
from src.pg_models.transfer import Transfer
from src.pg_models.controller import Controller
from src.pg_models.nominator import Nominator
from src.pg_models.validator import Validator
from src.pg_models.validator_to_nominator import ValidatorToNominator
#from src.event_handlers_pg import SystemEventHandler, BalancesEventHandler, StakingEventHandler, ClaimsEventHandler
from sqlalchemy.exc import IntegrityError
from src.node_connection import handle_one_block
from substrateinterface import SubstrateInterface
import ssl
import src.utils as utils
class PGBlockHandler:
    def __init__(self, session):
        self.session = session


    def handle_blocks(self,start, end):
        for i in range(start, end+1):
            with open(f"small_block_dataset/{i}.json", "r") as f:
                data = json.loads(f.read())  
            self.handle_full_block(data)
            #self.session.commit()

    def handle_node_connection_blocks(self,start,end):
        for i in range(start, end+1):
            
            block = handle_one_block(i)
            with open(f"small_block_dataset/{i}.json", "w+") as f:
                f.write(json.dumps(block, indent=4))
            with Driver().get_driver().begin():
                self.handle_full_block(block)
            #Driver().get_driver().commit()

    def handle_full_block(self,data):
        block = self.insert_block(data)
        extrinsics= self.handle_extrinsics_and_events(block,data)
        

    def insert_block(self,data):
        return Block.create(data)

    def handle_extrinsics_and_events(self,block,data) -> List[Extrinsic]:
        events_data = data["events"]

        extrinsics = []
        events = []
        self.staked_this_block = 0

        if len(data['extrinsics']) == 1 and len(events_data) > 2: # Todo: handle differently,
            """
            This was done because some blocks contain 0 extrinsics, 
            however they contain events that require handling
            """
            start = 0
            logging.warning(f"strange block {data['number']}")
        else:
            start = 1
            current_events_data = self.handle_events(events_data, 0)
            events = []
            for event_data in current_events_data:
                event = Event.create(event_data, None, block.block_number)
                self.handle_special_events(event)
        for i in range(start, len(data["extrinsics"])):
            """
            #index 0 is reserved for the timestamp transaction in extrinsics.
            
            if i in 0:
                timestamp = extrinsic_data["call"]["call_args"][0]["value"]
                print(timestamp)
                continue
            
            #index 1 is for paraInherents which probably have to be handled differently
            if i == 1:
                continue
            """
            #TODO make a parainherent check here
            extrinsic_data = data["extrinsics"][i]
            # an extrinsic_hash of None indicates ParaInherent transactions or Timestamp transactions
            # timestamp is already handled above
            current_events_data = self.handle_events(events_data, i)
            #last event denotes if ectrinsic was successfull
            #was_successful = current_events[-1].event_name == "ExtrinsicSuccess"
            extrinsic = Extrinsic.create(block, extrinsic_data,current_events_data)
            #events = [Event.create(event_data,extrinsic.id,block.block_number) for event_data in current_events_data]
            current_events = []
            for event_data in current_events_data:
                current_event = Event.create(event_data, extrinsic.id, block.block_number)
                self.handle_special_events(current_event)
                current_events.append(current_event)

            events.append(current_events)
            #if event['event_id'] in ['EraPayout', 'EraPaid'] and event['module_id'] == 'Staking':
            
            self.handle_special_extrinsics(block, extrinsic, current_events)
         
            
            #self.special_event(block, extrinsic, current_events)

            extrinsics.append(extrinsic)
            


        #if len(extrinsics)> 0:
        #    return extrinsics[0]
        Aggregator.create(block, extrinsics, events, self.staked_this_block)
        return extrinsics


    def handle_events(self,events, extrinsic_idx) -> List[Event]:
        """
            Iterates through events, selects those that have the same extrinsic_idx as the given one
            stores them in the db and returns all found events


            The events correspond to the transactions based on the order the transactions were executed
            The last event of a transaction indicates if the transaction was executed successfully
            i.e. the first transaction (timestamp) with index 0 has one event (with extrinsic_id 0) that indicates if it was successfull.
            an extrinsic (lets say it was extrinsic n) that sends DOT to an other account has multiple events (all with the same extrinic_id = n-1)

        """
        current_events = []
        for event_data in events:
            if extrinsic_idx == 0:
                extrinsic_idx = None
            if event_data["extrinsic_idx"] == extrinsic_idx:
                current_events.append(event_data)



        return current_events


    def insert_event(self,event_data):
        """
        Stores event data in db
        """

        event_data.pop("event")
        
        event_data.pop("event_index")
        event = Event(
            event_order_id = event_data["extrinsic_idx"], #denotes in which order the events happened. given n events the first event in block has 0 last event has n-1
            phase = event_data["phase"],
            module_name =  event_data["module_id"],
            event_name =  event_data["event_id"],
            attributes = event_data["attributes"],
            topics = event_data["topics"]
    
        )

        return event


    def handle_special_extrinsics(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        Each event has some implications on the overall data model. This function here differentiates between
        the different modules and then uses a event handler class to handle the specific event.
        e.g. the event "NewAccount" of the "Systems" module means that we have to create a new Account entry.

        Since not all data relevant for us is contained in the event data (sometimes we additionally need to know the blocknumber or time)
        we use the whole block.
        """

        print(f"{extrinsic.module_name}({extrinsic.function_name})")
        if not extrinsic.was_successful:
            return
        if(extrinsic.module_name == "Balances" and extrinsic.function_name in ["transfer", "transfer_keep_alive,transfer_all","force_transfer"]):
            return self.__handle_transfer(block, extrinsic, events)
        
        elif(extrinsic.module_name == "Staking" and extrinsic.function_name in ["bond", "bond_extra"]):
            return self.__handle_bond(block, extrinsic, events)

        elif(extrinsic.module_name == "Staking" and extrinsic.function_name == "set_controller"):
            return self.__handle_set_controller(block, extrinsic, events)
        elif(extrinsic.module_name == "Staking" and extrinsic.function_name == "set_payee"):
            return self.__handle_set_payee(block, extrinsic, events)
        elif(extrinsic.module_name == "Staking") and extrinsic.function_name == "payout_stakers":
            return self.__handle_payout_stakers(block, extrinsic, events)
        elif(extrinsic.module_name == "Staking" and extrinsic.function_name == "validate"):
            self.__handle_validate(block, extrinsic, events)
        elif (extrinsic.module_name == 'Utility' and extrinsic.function_name in ['batch', 'as_derivative', 'batch_all']):
            return self.__handle_batch(block, extrinsic, events)
        elif (extrinsic.module_name == "Proxy" and extrinsic.function_name == "proxy"):
            return self.__handle_proxy(block, extrinsic, events)
        elif (extrinsic.module_name == "Proxy" and extrinsic.function_name == "add_proxy"):
            return self.__handle_add_proxy(block, extrinsic,events)
        elif (extrinsic.module_name == "Claims" and extrinsic.function_name in ["claim", "attest"]):
            return self.__handle_claim(block, extrinsic, events)
        
        elif (extrinsic.module_name == "Sudo" and extrinsic.function_name in ["sudo","sudo_as"]):
            return self.__handle_sudo(block, extrinsic, events)

        
    def __handle_transfer(self, block: Block, extrinsic: Extrinsic, events: List[Event]):
        from_account = Account.get(extrinsic.account)

        # another sudo edge case. The sudo module can send money from an unowned account to another
        # sometimes it sends from account a to account a which doesn't make any sense.
        if extrinsic.function_name == "force_transfer":
            to_address = extrinsic.call_args[1]["value"].replace("0x","")
            #sending itself money, no need to handle that
            if to_address == extrinsic.call_args[0]["value"]:
                return
        else:
            to_address = extrinsic.call_args[0]["value"].replace("0x","")
        

        to_account = Account.get_from_address(to_address)
        if not to_account:
            to_account = Account.create(to_address)
        # Get amount transferred from 'Transfer' event
        amount_transferred = None
        for event in events:
  
            if event.event_name == 'Transfer':
                from_address = utils.extract_event_attributes_from_object(event,0)
                #In case of a proxy or sudo call the sender of dot is not the creator of the extrinsic
                if(from_account.address is not from_address):
                    from_account = Account.get_from_address(from_address)
                    if from_account is None:
                        from_account = Account.create(from_address)
                amount_transferred = utils.extract_event_attributes_from_object(event,2)

        # Create new balances
        if extrinsic.function_name == "force_transfer":
            amount_transferred = int(extrinsic.call_args[2]["value"])
        if from_account.id == to_account.id:
            amount_transferred = 0
        if amount_transferred is None:
            amount_transferred = extrinsic.call_args[1]["value"]
        from_balance = Balance.create(from_account, extrinsic, transferable=-(amount_transferred+extrinsic.fee), executing=True)
        to_balance = Balance.create(to_account, extrinsic,transferable=amount_transferred)
        
        transfer = Transfer.create(
            block_number=block.block_number,
            from_account=from_account,
            to_account=to_account,
            from_balance=from_balance,
            to_balance=to_balance,
            value=amount_transferred,
            extrinsic=extrinsic,
            type=extrinsic.function_name
        )
    
    def __handle_bond(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        from_account = Account.get(extrinsic.account)
        
        if extrinsic.function_name == "bond":
            #amount_transferred = extrinsic.call_args[1]["value"]
            for event in events:
                if event.module_name == "Staking" and event.event_name == "Bonded":
                    amount_transferred = utils.extract_event_attributes_from_object(event,1)
            controller_address = extrinsic.call_args[0]["value"]
            controller_account = Account.get_from_address(controller_address)
            reward_destination = extrinsic.call_args[2]["value"]
            if isinstance(reward_destination,dict):
                reward_destination = reward_destination["Account"]


            if not controller_account:
                controller_account = Account.create(controller_address)
            Controller.create(controller_account, from_account)
        elif extrinsic.function_name == "bond_extra":
            amount_transferred = extrinsic.call_args[0]["value"]
        else:
            raise NotImplementedError()
        
        old_balance = Balance.get_last_balance(from_account)
        new_balance = Balance.create(from_account, extrinsic,transferable=-(extrinsic.fee+amount_transferred) ,bonded=amount_transferred, executing=True)
        
        Transfer.create(
            block_number=block.block_number,
            from_account=from_account,
            to_account=from_account,
            from_balance=old_balance,
            to_balance=new_balance,
            value=amount_transferred,
            extrinsic=extrinsic,
            type=extrinsic.function_name
        )
        self.staked_this_block += amount_transferred

    def __handle_set_controller(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        controlled_account = Account.get(extrinsic.account)
        controller_address = extrinsic.call_args[0]["value"]
        controller_account = Account.get_from_address(controller_address)
        if controller_account is None:
            controller_account = Account.create(controller_address)
        
        Controller.create(controller_account, controlled_account)
    
    def __handle_set_payee(self, block: Block, extrinsic: Extrinsic, events: List[Event]):

        from_account = Account.get(extrinsic.account)
        reward_destination = extrinsic.call_args[0]["value"]
        if type(reward_destination) is dict:
            reward_destination = reward_destination["Account"]
        from_account.reward_destination = reward_destination
        
        Account.save(from_account)

    def handle_special_events(self,event: Event):
        """
        Certain features, like an era change, are only captured in events.
        """
        # Denotes that a new era has started. Note that EraPayout and EraPaid are the same event, they just got
        # renamed after some time.
        # From the following event we get the total reward of the last era

        if event.event_name in ['EraPayout', 'EraPaid'] and event.module_name == 'Staking':
            validator_pool = ValidatorPool.create(event)
            return
            substrate = self.create_substrate_connection()
            result = substrate.query(
                module='Staking',
                storage_function='ErasRewardPoints',
                params=[validator_pool.era]
            )

    def __handle_payout_stakers(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        validator_stash = extrinsic.call_args[0]["value"]
        era = extrinsic.call_args[1]["value"]
        validator_account = Account.get_from_address(validator_stash)
        
        validator = Validator.create(validator_account,era)
        for event in events:
            if event.event_name == "Reward":
                nominator_reward = event.attributes[1]['value']
                nominator_address = event.attributes[0]['value']
                
                nominator_account = Account.get_from_address(nominator_address)
                if nominator_account is None:
                    nominator_account = Account.create(nominator_address)
                from_balance = Balance.get_last_balance(validator_account)
                
                transfer = None
                if nominator_address == validator_stash:
                    if validator_account.reward_destination in [None, 'Stash', 'Controller', 'Account']:
                        to_balance = validator_account.update_balance(extrinsic,transferable=nominator_reward)
                        transfer = Transfer.create(block.block_number, None,nominator_account,None,to_balance,nominator_reward,extrinsic,"Reward")
                        from_balance = to_balance
                    elif validator_account.reward_destination in ['Staked']:
                        to_balance = validator_account.update_balance(extrinsic,bonded=nominator_reward)
                        transfer = Transfer.create(block.block_number, None,nominator_account,None,to_balance,nominator_reward,extrinsic,"Reward")
                        self.staked_this_block += nominator_reward
                    else:
                        external_account = Account.get_from_address(nominator_account.reward_destination)
                        if external_account is None:
                            external_account = Account.create(nominator_account.reward_destination)
                        to_balance = external_account.update_balance(extrinsic, transferable=nominator_reward)
                        transfer = Transfer.create(block.block_number, None,external_account,None,to_balance,nominator_reward,extrinsic,"Reward")

                else:
                    if nominator_account.reward_destination in [None, 'Stash', 'Controller', 'Account']:
                        from_balance = validator_account.update_balance(extrinsic, transferable=-nominator_reward)
                        to_balance = nominator_account.update_balance(extrinsic, transferable=nominator_reward)
                        transfer = Transfer.create(block.block_number, None,nominator_account,None,to_balance,nominator_reward,extrinsic,"Reward")
                    elif nominator_account.reward_destination in ['Staked']:
                        from_balance = validator_account.update_balance(extrinsic, transferable=-nominator_reward)
                        to_balance = nominator_account.update_balance(extrinsic,bonded=nominator_reward)
                        transfer = Transfer.create(block.block_number, None,nominator_account,None,to_balance,nominator_reward,extrinsic,"Reward")
                        self.staked_this_block += nominator_reward
                    else:
                        external_account = Account.get_from_address(nominator_account.reward_destination)
                        if external_account is None:
                            external_account = Account.create(nominator_account.reward_destination)
                        to_balance = external_account.update_balance(extrinsic, transferable=nominator_reward)
                        transfer = Transfer.create(block.block_number, None,external_account,None,to_balance,nominator_reward,extrinsic,"Reward")

                
                nominator = Nominator.create(
                    nominator_account,
                    validator,
                    nominator_reward,
                    transfer,
                    era
                    )
                Account.save(nominator_account)
                #Nominator.save(nominator)
                Validator.save(validator)
                vtn = ValidatorToNominator.get(validator,nominator,era)
                if vtn is None:
                    ValidatorToNominator.create(nominator, validator, era)


    def __handle_batch(self, block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        Some extrinsic are of type batch, meaning they execute multiple function calls in one extrinsic.
        This function iterates through those function calls,creates an extrinsic entry for them and calls
        the handle_special_extrinsics function in case one is special. 
        """

        event_start = 0
        event_end = len(events)
        for sub_extrinsic_data in extrinsic.call_args[0]["value"]:
            for i in range(event_start, event_end):
                if events[i].module_name == "Utility":
                    if events[i].event_name == "ItemCompleted":
                        was_successful = True
                        break
                    elif events[i].event_name == "ItemFailed":
                        was_successful = False
                        break
                    elif events[i].event_name == "BatchInterrupted":
                        was_successful = False
                        break
                    elif events[i].event_name == "BatchCompleted":
                        was_successful = True
                        break
                elif events[i].event_name == "ProxyExecuted" and events[i].module_name == 'Proxy':
                    was_successful = True
                    break
                
                # True Horror, an encapsulation of type Sudo->Batch gives no indication as to which events
                # belong to which item of the batch. we have to handle those by hand.
                elif block.block_number in [240853,240984,372203,500796]:
                    was_successful=True
                    i=i+2 #take 3 events
                    break
                elif events[i].module_name == "Sudo" and events[i].event_name == "SudoAsDone":
                    was_successful = utils.extract_event_attributes_from_object(events[i],0)
                    break
            
            sub_events = events[event_start:i+1]
            event_start = i+1
            sub_extrinsic = Extrinsic.create_from_batch(block, sub_extrinsic_data, events, extrinsic, was_successful)
            self.handle_special_extrinsics(block, sub_extrinsic, sub_events)

    def __handle_proxy(self, block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        A proxy transaction, as the name suggest, executes an extrinsic from another account then the one
        executing the proxy.
        We extract the proxy 'call_args', create a new extrinsic with the other accounts address and call the
        handle_special_extrinsic function.
        """
        
        proxied_extrinsic = Extrinsic.create_from_proxy(block, extrinsic,events)
        self.handle_special_extrinsics(block, proxied_extrinsic, events)

    def __handle_claim(self, block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        Before polkadot was fully functional one could buy DOT with Ethereum. Using the Claims(claim) functionality
        one can receive the bought DOT.
        This function creates the new account in the DB and transfers the claimed DOT into it.
        """
        #if extrinsic.function_name != "Attest":
        #    address = utils.convert_public_key_to_polkadot_address(extrinsic.call_args[0]["value"])
        #else:
        #    address = events[-1]
        amount_transfered = 0
        for event in events:
            if event.module_name == "Claims" and event.event_name == "Claimed":
                amount_transfered = utils.extract_event_attributes_from_object(event,2)
                eth_address = utils.extract_event_attributes_from_object(event,1)
                address = utils.convert_public_key_to_polkadot_address(utils.extract_event_attributes_from_object(event,0))
                eth_account = Account.create(eth_address, note=address)
            
                

        account = Account.get_from_address(address)
        if account is None:
            account = Account.create(address)
        
        last_balance = Balance.get_last_balance(account)

        new_balance = account.update_balance(
            extrinsic,
            transferable=amount_transfered,
        )

        Transfer.create(block.block_number,eth_account, account, last_balance,new_balance,amount_transfered,extrinsic, "Claim")

    def __handle_sudo(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        A sudo call wraps around another call. We extract the call inside the sudo call and create a new extrinsic
        object out of it. Then we also execute handle_special_extrinsics if needed.
        """
        proxied_extrinsic = Extrinsic.create_from_sudo(block, extrinsic,events)
        self.handle_special_extrinsics(block, proxied_extrinsic, events)


    def __handle_add_proxy(self, block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        A proxy account reserves 20.008 DOT (https://wiki.polkadot.network/docs/learn-proxies#proxy-deposits)

        """
        #TODO handle proxy relation
        for event in events:
            if event.module_name == "Balances" and event.event_name == "Reserved":
                account = Account.get(extrinsic.account)
                amount = utils.extract_event_attributes_from_object(event,1)
                
                last_balance = Balance.get_last_balance(account)
                new_balance = account.update_balance(
                    extrinsic,
                    transferable=-amount,
                    reserved=amount
                    )
                Transfer.create(
                    block.block_number,
                    account,
                    account,
                    last_balance,
                    new_balance,
                    amount,
                    extrinsic,
                    "Reserved"
                    )
                break
    def __handle_validate(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        commission = extrinsic.call_args[0]["value"]["commission"]
        ValidatorConfig.create(extrinsic.account, commission, block)
        
