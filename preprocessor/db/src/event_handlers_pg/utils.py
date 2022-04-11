import logging
from ast import arg
from copy import deepcopy
from mongoengine.errors import DoesNotExist
from src.pg_models import Account, Balance, Block, Extrinsic, Event
from sqlalchemy import select


def decorator_factory(decorator):
    """
    Meta decorator
    Is used to decorate other decorators such that they can have passed an argument
    e.g. 
    @decorator(argument)
    would not work if decorator isn't decorated with this decorator
    It is used mostly for the event_error_handling such that we can decorate a function with an exception and
    log it if something bad happened
    """

    def layer(error, *args, **kwargs):

        def repl(f, *args, **kwargs):
            return decorator(f, error, *args, **kwargs)

        return repl

    return layer

@decorator_factory
def event_error_handling(function, error, *args, **kwargs):
    """
    This decorator is used for error handling and logging

    Usage:
    @event_error_handling(LikelyExceptionThatShouldBeLogged)
    def foo(bar):
        ...
    
    """
    def wrapper(block, extrinsic, event, *args, **kwargs):

        try:
            return function(block, extrinsic, event, *args, **kwargs)
        except error as e:
            logging.error(f"{error.__name__}: {e}\t {function.__name__} failed at block {block.block_number} in extrinsic "
                          f"{extrinsic.extrinsic_hash} in event {event.extrinsic_idx}, "
                          f"{event.module_id}: {event.event_id}, {event.attributes[0]['value']}")

    return wrapper


def get_account(address: str, block_number: int,session):
    

    stmt = select(Account).where(Account.address == address)
    account = list(session.execute(stmt))
    if len(account) == 0:
        balance = Balance(
            transferable=0,
            reserved=0,
            bonded=0,
            unbonding=0,
            block_number=block_number,
            account=address
        )
        account = Account(
            address=address,
            account_index=None,
            nonce=None,
            role=None)

        session.add(account)
        session.commit()
        session.add(balance)
        session.commit()
        return account

    return account[0][0]


def transfer(from_account: Account, to_account: Account, value: int, from_subbalance: str, to_subbalance: str, session):

    stmt = select(Balance).where(Balance.account == from_account.address)
    from_account_balance = deepcopy(list(session.execute(stmt))[-1])[0]
    print("ey")
    print(to_account)
    stmt = select(Balance).where(Balance.account == to_account.address)
    to_account_balance = deepcopy(list(session.execute(stmt))[-1])[0]


    #from_account_balance.id = None
    #to_account_balance.id = None
    print(from_account_balance)
    from_updated_value = getattr(from_account_balance, from_subbalance) - value
    setattr(from_account_balance, from_subbalance, from_updated_value)
    to_updated_value = getattr(to_account_balance, to_subbalance) + value
    setattr(to_account_balance, to_subbalance, to_updated_value)

    session.add(from_account_balance)
    session.add(to_account_balance)
    session.commit()
    return from_account, to_account
