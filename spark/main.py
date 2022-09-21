import argparse
from sys import set_coroutine_origin_tracking_depth
import time
from pyspark.sql import SparkSession



queries_postgres = {
    "get_balances_all": "select * from balance",
    "get_balances_year": "select * from balance b where b.block_number > (select greatest(max(b.block_number) - 5256000 , 0) from balance b)",
    "get_balances_month": "select * from balance b where b.block_number > (select greatest(max(b.block_number) - 432000 , 0) from balance b)",
    "get_balances_day": "select * from balance b where b.block_number > (select greatest(max(b.block_number) - 14400 , 0) from balance b)",
    "get_transfers_all": "select * from transfer",
    "get_accounts_all": "select * from account",
    "get_blocks_all": "select * from block",
    "get_transfers_and_accounts": "select * from transfer t inner join account a1 on a1.address = t.from_address inner join account a2  on a2.address = t.to_address",
    "get_last_balances": "Select b2.* from balance b2 inner join (select b.account, max(b.block_number) as block_number from balance b group by b.account) as b1 on b1.account=b2.account and b1.block_number=b2.block_number",
    "get_nominator_rewards": "select an.address as nominator, av.address as validator,n.reward as reward,an.reward_destination as reward_destination,n.era as era from nominator n inner join validator v on v.id = n.validator inner join account an on an.id = n.account inner join account av on av.id = v.account"
}

queries_neo4j = {
    "get_transactions_all": "match(t:Transaction) return t",
    "get_blocks_and_validators": "match(b:Block)-[:HAS_AUTHOR]-(v:Validator)-[:IS_VALIDATOR]-(a:Account) return b,v,a",
    "get_validatorpools_validators_nominators": "match(v:ValidatorPool)-[:HAS_VALIDATOR]-(n:Validator)-[:HAS_NOMINATOR]-(g:Nominator) return v,n,g",
    "get_all_on_block": "match(b:Block)-[*1]-() return b"
}


def init_sparksession(query: str, db: str):
    print(query)
    print(db)
    if db == "p":
        print('postgres_job')
        url = "jdbc:postgresql://172.23.149.214:5432/map"
        return \
            SparkSession \
            .builder \
            .appName("Polkadot Pyspark Postgres") \
            .config("spark.jars", "./postgresql-42.2.6.jar") \
            .getOrCreate() \
            .read \
            .format("jdbc") \
            .option("url", url) \
            .option("user", "mapUser") \
            .option("password", "mapmap") \
            .option("driver", "org.postgresql.Driver") \
            .option("query", query) \
            .load()
    else:
        print('graph_job')
        url = 'bolt://127.0.0.1:7687'
        user = "neo4j"
        password = "mapmap"
        return \
            SparkSession \
            .builder \
            .appName("Polkadot Pyspark neo4j") \
            .config("spark.jars", "./neo4j-connector-apache-spark_2.12-4.1.2_for_spark_3.jar") \
            .config("neo4j.url", "bolt://localhost:7687") \
            .config("neo4j.authentication.type", "basic") \
            .config("neo4j.authentication.basic.username", user) \
            .config("neo4j.authentication.basic.password", password) \
            .getOrCreate()\
            .read \
            .format("org.neo4j.spark.DataSource") \
            .option("url", url) \
            .option("user", user) \
            .option("password", password) \
            .option("query", query)\
            .load()




def main(args):
    print(args)
    start = time.perf_counter()
    if args.query is not None:
        query = args.query
    else:
        if args.database == "p":
            query = queries_postgres[args.preset]
        else:
            query = queries_neo4j[args.preset]
    spark = init_sparksession(query, db=args.database)
    spark.show(
    )
    spark.time(spark.show())
    exit()
    if args.save:
        if args.name is None:
            name = "untitled"
        else:
            name = args.name
        spark.write.parquet(path=f"./results/{name}.parquet")
        end = time.perf_counter()
        print(end - start)


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q",   "--query",                              help="enter SQL query",           type=str)
    parser.add_argument("-u",   "--url",                          help="default: localhost",        type=str)
    parser.add_argument("-n",   "--name",                               help="name for file results",     type=str)
    parser.add_argument("-pre", "--preset",                           help="choose predefined query",   type=str)
    parser.add_argument("-p",   "--plot",    action='store_true',       help="plot of graph")
    parser.add_argument("-s",   "--save",    action='store_true',       help="Save to /results")
    parser.add_argument("-d",  "--database",                           help="p=postgres or n=neo4j")
    return parser.parse_args()





if __name__ == "__main__":
    arguments = argparser()
    if arguments.query is None and arguments.preset is None:
        raise UserWarning("A predefined or userdefined query via flags {-q, -pre} is required")
        exit()
    if arguments.query is not None and arguments.preset is not None:
        raise UserWarning("Cannot process predefined AND userdefined query. Select one and remove other")
        exit()

    main(arguments)







