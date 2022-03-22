import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType, MongoengineConnectionField
from src.models import Block as BlockModel


class BlockType(MongoengineObjectType):
    class Meta:
        model = BlockModel
        interfaces = (Node,)


class Query(graphene.ObjectType):
    node = Node.Field()
    block = graphene.List(BlockType)

    def resolve_block(self, info):
        return BlockModel.objects.all()

schema = graphene.Schema(query=Query, types=[BlockType])