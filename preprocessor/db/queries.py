import graphene

from graphene_mongo import MongoengineObjectType

from models import Block as BlockModel

class Block(MongoengineObjectType):
    class Meta:
        model = BlockModel

class Query(graphene.ObjectType):
    blocks = graphene.List(Block)
    
    def resolve_blocks(self, info):
    	return list(BlockModel.objects.all())

block_schema = graphene.Schema(query=Query)