import argparse
from sys import set_coroutine_origin_tracking_depth
import time
from pyspark.sql import SparkSession


queries_postgres = {
    "get_nominator_rewards": """
        select 
            an.address as nominator,
            av.address as validator,
            n.reward as reward,
            an.reward_destination as reward_destination,
            n.era as era,n.stake as stake,
            v.total_stake as validator_total_stake,
            v.own_stake as validator_self_stake,
            v.commission as validator_commission
        from nominator n
            inner join validator v
                on v.id = n.validator
            inner join account an
                on an.id = n.account
            inner join account av
                on av.id = v.account
        ORDER by era, validator, nominator
    """,
    "get_nominator_rewards_address": """
        select
            an.address as nominator, 
            av.address as validator,
            n.reward as reward,
            an.reward_destination as reward_destination,
            n.era as era,
            n.stake as stake,
            v.total_stake as validator_total_stake,
            v.own_stake as validator_self_stake,
            v.commission as validator_commission
        from nominator n 
            inner join validator v 
                on v.id = n.validator 
            inner join account an 
                on an.id = n.account 
            inner join account av 
                on av.id = v.account
        WHERE an.address='REPL0' 
        ORDER by era, validator, nominator
    """,
    "get_validator_pools": "select * from validator_pool",

    "get_validator_pool_at_era": "select * from validator_pool where era=REPL0",
    "get_balances_at_block": """
        SELECT DISTINCT ON (address)
            address,
            transferable, 
            reserved,
            bonded,
            unbonding,
            b.block_number
        FROM balance b
            INNER JOIN account a
                on a.id = b.account
        WHERE b.block_number < REPL0
        ORDER BY address, b.block_number DESC
    """,
    "get_balances_for_address": """
        SELECT
            a.address,
            b.transferable, 
            b.reserved,
            b.bonded,
            b.unbonding,
            b.block_number
        FROM balance b
            INNER JOIN account a
                ON a.id = b.account
        WHERE a.address = 'REPL0'
        ORDER BY b.block_number
    """,
    "get_aggregators": """
        SELECT * 
        FROM aggregator
        ORDER BY block_number DESC
    """,
    "get_aggregator_at_block": """
        SELECT * 
        FROM aggregator
        WHERE block_number=REPL0
    """,
    "get_aggregator_diff": """
        select block_number, 
            total_extrinsics - lead(total_extrinsics) over (order by block_number DESC) as delta_extrinsics,
            total_events - lead(total_events) over (order by block_number DESC) as delta_events,
            total_accounts - lead(total_accounts) over (order by block_number DESC) as delta_accounts,
            total_transfers - lead(total_transfers) over (order by block_number DESC) as delta_transfers,
            total_staked - lead(total_staked) over (order by block_number DESC) as delta_staked
        
        from aggregator
        where block_number in (REPL0, REPL1)
        limit 1
    """,
    "get_transfer_network_for_account": """
    SELECT 
        af.address as from_address, 
        at.address as to_address
    FROM transfer t
        INNER JOIN account af
            ON af.id = t.from_account
        INNER JOIN account at
            ON at.id = t.to_account
    WHERE af.address = 'REPL0'
    OR at.address = 'REPL0'
    """
}

queries_neo4j = {
    "get_transactions_all": "match(t:Transaction) return t",
    "get_blocks_and_validators": "match(b:Block)-[:HAS_AUTHOR]-(v:Validator)-[:IS_VALIDATOR]-(a:Account) return b,v,a",
    "get_validatorpools_validators_nominators": "match(v:ValidatorPool)-[:HAS_VALIDATOR]->(n:Validator)-[:HAS_NOMINATOR]->(g:Nominator) return v,n,g",
    "get_all_on_block": "match(b:Block)-[*1]-() return b",
    "get": "match(v:ValidatorPool)-[:HAS_VALIDATOR]->(n:Validator) return v,n",
    "get_transfernetwork": "match(account:Account)-[transfer_to:TRANSFER_TO]->(b:Account) return account,b,transfer_to"
}


def init_sparksession(query: str, db: str):
    print(query)
    print(db)
    if db == "p":
        print('postgres_job')
        url = "jdbc:postgresql://172.23.149.214:5432/map3"
        return \
            SparkSession \
            .builder \
            .config("spark.driver.memory", "15g") \
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
        url = 'bolt://172.23.149.214:7687'
        user = "neo4j"
        password = "mapmap"
        return \
            SparkSession \
            .builder \
            .config("spark.driver.memory", "15g") \
            .appName("Polkadot Pyspark neo4j") \
            .config("spark.jars", "./neo4j-connector-apache-spark_2.12-4.1.2_for_spark_3.jar") \
            .config("neo4j.url", url) \
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
    if args.args:
        for i, val in enumerate(args.args):
            query = query.replace(f"REPL{i}", val)

    spark = init_sparksession(query, db=args.database)
    spark.show(
    )
    if args.save:

        spark.write.csv(path=f"./results/{args.save}.csv")
    end = time.perf_counter()
    print(f"Took {end - start}")


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q",   "--query",                              help="enter SQL/cypher query",           type=str)
    parser.add_argument("-u",   "--url",                          help="default: localhost",        type=str)
    parser.add_argument("-n",   "--name",                               help="name for file results",     type=str)
    parser.add_argument("-p", "--preset",                           help="choose predefined query",   type=str)
    parser.add_argument("-s",   "--save",          help="Save to /results. Add a filename as an argument", type=str)
    parser.add_argument("-d",  "--database",                           help="p=postgres or n=neo4j")
    parser.add_argument("-a", "--args",nargs='+')
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







