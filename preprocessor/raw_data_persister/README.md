# raw_data_persister
This is the the raw_data_persister. Its job is to receive raw data from Apache Kafka and store it in our postgres database.

## normal usage
Use the same environment as in the `db` folder one level above.

Use `python setup_pg.py` to set up all the relevant tables.

Use `python main.py` to start the raw_data_persister.

## missing blocks
There exists the case that some blocks are not stored in the raw data database (reasons could be a problem with the producer such as a websocket exception, a problem with kafka or others). Should you notice that blocks are missing do as follows:
* Execute the following sql query to get all the block numbers that are missing and store them as csv.
```
SELECT nr.i as missing_index
FROM (
  SELECT i
  FROM generate_series(1, (SELECT MAX(block_number) FROM raw_data)) i
) nr
LEFT JOIN raw_data t1 
    ON nr.i = t1.block_number
WHERE t1.block_number is null;
```
* Pull the file here and name it missing_data.csv.
* in the `main.py` file change the `mode` variable to `"node"`.
* Start the program via `python main.py`.
* The program will now query the node directly to get the missing data and store them.