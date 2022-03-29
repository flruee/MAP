import graphene
from graphene.relay import Node
from graphene.types.scalars import BigInt
from graphene_mongo import MongoengineObjectType
from src.models import (
    Block as BlockModel,
    Extrinsic as ExtrinsicModel,
    Header as HeaderModel,
    Account as AccountModel,
    Balance as BalanceModel,
    Locked as LockedModel,
    Transfer as TransferModel

)



class BlockType(MongoengineObjectType):
    class Meta:
        model = BlockModel
        #interfaces = (Node,)

class HeaderType(MongoengineObjectType):
    class Meta:
        model = HeaderModel
        #interfaces = (Node,)

class ExtrinsicType(MongoengineObjectType):
        class Meta:
            model = ExtrinsicModel


class AccountType(MongoengineObjectType):

    class Meta:
        model = AccountModel


class BalanceType(MongoengineObjectType):
    class Meta:
        model = BalanceModel

class LockedType(MongoengineObjectType):
    class Meta:
        model = LockedModel

class TransferType(MongoengineObjectType):
    class Meta:
        model = TransferModel
class Query(graphene.ObjectType):
    node = Node.Field()
    block = graphene.List(BlockType)
    header = graphene.List(HeaderType)
    extrinsic = graphene.List(ExtrinsicType)
    account = graphene.List(AccountType)
    transfer = graphene.List(TransferType)

    def resolve_block(self, info):
        return BlockModel.objects.all()

    def resolve_header(self, info):
        return HeaderModel.objects.all()

    def resolve_extrinsics(self, info):
        return ExtrinsicModel.objects.all()
    
    def resolve_account(self, info):
        return AccountModel.objects.all()

    def resolve_balance(self, info):
        return BalanceModel.objects.all()

    def resolve_locked(self, info):
        return LockedModel.objects.all()

    def resolve_transfer(self, info):
        print("ho")
        return TransferModel.objects.all()

schema = graphene.Schema(query=Query)