import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from src.models import Block as BlockModel, Extrinsic as ExtrinsicModel, Header as HeaderModel, Account as AccountModel


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

class Query(graphene.ObjectType):
    node = Node.Field()
    block = graphene.List(BlockType)
    header = graphene.List(HeaderType)
    extrinsic = graphene.List(ExtrinsicType)
    account = graphene.List(AccountType)


    def resolve_block(self, info):
        return BlockModel.objects.all()

    def resolve_header(self, info):
        return HeaderModel.objects.all()

    def resolve_extrinsics(self, info):
        return ExtrinsicModel.objects.all()
    
    def resolve_account(self, info):
        return AccountModel.objects.all()


schema = graphene.Schema(query=Query)