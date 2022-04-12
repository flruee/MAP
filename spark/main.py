from pyspark.sql import SparkSession



if __name__ == "__main__":
    print("PySpark Structured Streaming with Kafka Application Started …")
    spark = SparkSession \
        .builder \
        .appName("PySpark Structured Streaming with Kafka Polkadot") \
        .master("local[*]") \
        .getOrCreate()
    stream_detail_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "polkadotBlockData") \
        .option("startingOffsets", "latest") \
        .load()

    stream_detail_df = stream_detail_df.selectExpr(
    "CAST(key AS STRING)", "CAST(value AS STRING)", "timestamp")

    """
    # One way of having the customer data in a table
    # customer_data_df=spark.sql(“SELECT * FROM SPA_ASSGN_WAREHOUSE.MYMALL_CUSTOMER_DETAILS”)
    # Other way is to create a dataframe from the csv file placed in HDFS location
    customer_data_df=spark.read.format(“csv”).option(“header”,”true”).option(“delimiter”,”,”).load(“/home/cloudera/workspace/projects/SPAAssignment/data/customer.csv”)
    print(“Printing Schema of customer_data_df: “)
    customer_data_df.printSchema()
    # Construct a streaming DataFrame that reads from testtopic
    stream_detail_df = spark \
    .readStream \
    .format(“kafka”) \
    .option(“kafka.bootstrap.servers”, KAFKA_BOOTSTRAP_SERVERS_CONS) \
    .option(“subscribe”, KAFKA_INPUT_TOPIC_NAME_CONS) \
    .option(“startingOffsets”, “latest”) \
    .load()
    
    
    stream_detail_df = stream_detail_df.withColumn(‘Cust_id’, split_col.getItem(0))
    
    stream_detail_df = stream_detail_df.withColumn(‘IP address’, split_col.getItem(1))
    stream_detail_df = stream_detail_df.withColumn(‘Latitude’, split_col.getItem(2).cast(“float”))
    stream_detail_df = stream_detail_df.withColumn(‘Longitude’, split_col.getItem(3).cast(“float”))
    print(“Printing Schema of stream_detail_df: “)
    stream_detail_df.printSchema()
    
    #Obtaining distance in meters using longitude and latitude
    stream_detail_df = stream_detail_df.withColumn(‘a’, (
    pow(sin(radians(col(“Latitude”) — lit(MALL_LATITUDE)) / 2), 2) +
    cos(radians(lit(MALL_LATITUDE))) * cos(radians(col(“Latitude”))) *
    pow(sin(radians(col(“Longitude”) — lit(MALL_LONGITUDE)) / 2), 2)
    )).withColumn(“distance”, atan2(sqrt(col(“a”)), sqrt(-col(“a”) + 1)) * 12742000)
    
    #Filtering customers based on distance
    stream_detail_df = stream_detail_df.drop(“a”)
    stream_detail_df = stream_detail_df.filter(col(“distance”) <= MALL_THRESHOLD_DISTANCE)
    #Joining Customer stream data with customer dataset
    stream_detail_df = stream_detail_df.join(customer_data_df,stream_detail_df.Cust_id == customer_data_df.CustomerID)
    #Discount and Coupon generation
    
    stream_detail_df = stream_detail_df.withColumn(“Discount”, when( (col(“Spending Score”) >= 85) | ((col(“Annual Income”) >=30000) & (col(“Spending Score”) >= 65)) , ‘40%’).when(((col(“Spending Score”) >= 65 ) & ( col(“Spending Score”) < 85 )) | ((col(“Annual Income”) >=20000) & (col(“Annual Income”) < 30000) & (col(“Spending Score”) >=45)), ‘30%’).when(((col(“Spending Score”) >= 45 ) & ( col(“Spending Score”) < 65)) | (col(“Annual Income”) >= 15000), ‘20%’).otherwise(“10%”))
    stream_detail_df = stream_detail_df.withColumn(“Coupon_Code”, lit(‘’.join(random.choice(string.ascii_uppercase+string.ascii_lowercase+string.digits) for _ in range(16))))
    # Write final result into console for debugging purpose
    customer_detail_write_stream = stream_detail_df \
    .writeStream \
    .trigger(processingTime=’1 seconds’) \
    .outputMode(“update”) \
    .option(“truncate”, “false”)\
    .format(“console”) \
    .start()
    # Output topic dataframe creation by selecting required columns
    
    final_stream_df = stream_detail_df.selectExpr(“CustomerID”,”distance”,”Discount”,”Coupon_Code”)
    
    final_stream_df = final_stream_df.withColumn(“key”,rand()*3)
    # Write key-value data from a DataFrame to a specific Kafka topic specified in an option
    customer_detail_write_stream_1 = final_stream_df \
    .selectExpr(“CAST(key AS STRING)”, “to_json(struct(*)) AS value”) \
    .writeStream \
    .format(“kafka”) \
    .option(“kafka.bootstrap.servers”, KAFKA_BOOTSTRAP_SERVERS_CONS) \
    .option(“topic”, KAFKA_OUTPUT_TOPIC_NAME_CONS) \
    .trigger(processingTime=’1 seconds’) \
    .outputMode(“update”) \
    .option(“checkpointLocation”, “/home/cloudera/workspace/SPAAssignment/chkpoint”) \
    .start()
    customer_detail_write_stream.awaitTermination()
    print(“PySpark Structured Streaming with Kafka Application Completed.”)
    
    """