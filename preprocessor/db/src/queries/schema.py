import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType, MongoengineConnectionField
from src.models import Block as BlockModel
from src.models import Header as HeaderModel


class BlockType(MongoengineObjectType):
    class Meta:
        model = BlockModel
        interfaces = (Node,)

class HeaderType(MongoengineObjectType):
    class Meta:
        model = HeaderModel
        interfaces = (Node,)


class Query(graphene.ObjectType):
    node = Node.Field()
    block = graphene.List(BlockType)
    header = graphene.List(HeaderType)

    def resolve_block(self, info):
        return BlockModel.objects.all()

    def resolve_header(self, info):
        return HeaderModel.objects.all()

schema = graphene.Schema(query=Query)