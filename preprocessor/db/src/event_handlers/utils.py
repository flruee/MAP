import logging
from ast import arg
from copy import deepcopy
from mongoengine.errors import DoesNotExist
from src.models import Account, Balance, Block, Extrinsic, Event


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


def get_account(address: str, block_number: int):
    try:
        account = Account.objects.get(address=address)
    except DoesNotExist:
        balance = Balance(
            transferable=0,
            reserved=0,
            bonded=0,
            unbonding=0,
            block_number=block_number
        )
        balance.save()
        account = Account(
            address=address,
            balances=[balance],
            extrinsics=[],
            transfers=[],
            vote=[],
            reward_slash=[],
            account_index=None,
            nonce=None,
            role=None)

        account.save()

    return account


def transfer(from_account: Account, to_account: Account, value: int, from_subbalance: str, to_subbalance: str):

    from_account_balance = deepcopy(from_account.balances[-1])
    if from_account == to_account:
        to_account_balance = from_account_balance
    else:
        to_account_balance = deepcopy(to_account.balances[-1])

    from_account_balance.id = None
    to_account_balance.id = None

    from_updated_value = getattr(from_account_balance, from_subbalance) - value
    setattr(from_account_balance, from_subbalance, from_updated_value)
    to_updated_value = getattr(to_account_balance, to_subbalance) + value
    setattr(to_account_balance, to_subbalance, to_updated_value)

    from_account.balances.append(from_account_balance)
    if from_account == to_account:
        pass
    else:
        to_account.balances.append(to_account_balance)

    from_account_balance.save()
    if from_account == to_account: # Todo: not sure if this check is necessary
        pass
    else:
        to_account_balance.save()
    return from_account, to_account
