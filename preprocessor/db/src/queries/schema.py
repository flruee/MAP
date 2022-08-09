import graphene
from graphene_mongo import MongoengineObjectType
from src.models import (
    Block as BlockModel,
    Extrinsic as ExtrinsicModel,
    Header as HeaderModel,
    Account as AccountModel,
    Balance as BalanceModel,
    Transfer as TransferModel
)


class BlockType(MongoengineObjectType):
    class Meta:
        model = BlockModel


class HeaderType(MongoengineObjectType):
    class Meta:
        model = HeaderModel


class ExtrinsicType(MongoengineObjectType):
    class Meta:
        model = ExtrinsicModel


class AccountType(MongoengineObjectType):
    class Meta:
        model = AccountModel

    def resolve_transfers(self, info, type=None):
        print("miau")
        print(info)
        print(type)
        return TransferModel.objects.all()

class BalanceType(MongoengineObjectType):
    class Meta:
        model = BalanceModel


class TransferType(MongoengineObjectType):
    class Meta:
        model = TransferModel


class Query(graphene.ObjectType):
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

    def resolve_transfer(self, info):
        print("eyy")
        return TransferModel.objects.all()
    
    def resolve_transfer_by_type(self, info, type):
        print("miau")
        return TransferModel.objects.filter(type=type)


schema = graphene.Schema(query=Query)
