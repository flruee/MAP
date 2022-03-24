


from src.models.models import Account, Block, Extrinsic, Event



class SystemEventHandler():

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "NewAccount":
            SystemEventHandler.__handle_newAccount(block, extrinsic, event)

    @staticmethod
    def __handle_newAccount(block: Block, extrinsic: Extrinsic, event: Event):
        
        account = Account(
            address = event.attributes[0]["value"],
            balance = [],
            basic_info = [],  
            extrinsics = [],
            transfers = [],
            vote = [],
            reward_slash = []
        )
        account.save()
