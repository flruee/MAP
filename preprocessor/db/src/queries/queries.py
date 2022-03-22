from dataclasses import field
from tkinter.messagebox import NO
import graphene
from graphene.relay import Node

from graphene_mongo import MongoengineObjectType, MongoengineConnectionField

from src.models import Block, Header

class BlockType(MongoengineObjectType):
    class Meta:
        model = Block
        #interfaces = (Node,)
        fields = ("hash")
    
    def resolve_block(self, info):
        print("mi")
        return list(Block.objects.all())

    """
    def resolve_header(self, info):
        blocks = list(Block.objects.all())
        headers = []
        for block in blocks:
            print("arg")
            print(block["header"]["extrinsicsRoot"])
            print("barg")
            headers.append(block["header"])
        print("hello2")
        print(headers[0]["extrinsicsRoot"])
        return headers
    """

class HeaderType(MongoengineObjectType):
    class Meta:
        model = Header
        interfaces = (Node,)
    
        

class Query(graphene.ObjectType):
    node = Node.Field()
    blocks = MongoengineConnectionField(BlockType)
    block = graphene.Field(BlockType)
    #headers = MongoengineConnectionField(HeaderType)

    #def resolve_blocks(self, info):
    #	return list(Block.objects.all())



block_schema = graphene.Schema(query=Query, types=[BlockType])