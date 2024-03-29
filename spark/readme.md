# instructions setup spark on server
## steps with * only have to be done once

## 1* create venv & install pyspark 
python3 -m venv .sparkenv
pip install pyspark

## 2* download postgresdriver
wget https://jdbc.postgresql.org/download/postgresql-42.2.6.jar

## 3 execute spark shell
.sparkenv/bin/spark-shell

## 4* on MAP_POLKA server, configure postgresql.conf 
listen_addr = add ip of MAP_Spark
## and* configure pg_hba.conf
append:
host    all             all             172.0.0.0/0             md5
## and* restart postgres server
sudo systemctl restart postgresql

## 5 in scala execute following commands:
:require postgresql-42.2.6.jar
import java.util.Properties
val url = "jdbc:postgresql://172.23.149.214:5432/mapPolka?user=mapUser&password=mapmap"
val connectionProperties = new Properties()
connectionProperties.setProperty("Driver", "org.postgresql.Driver")

## 6 define query and show it

val query1 = "(SELECT * FROM t1) as q1"
val query1df = spark.read.jdbc(url, query1, connectionProperties)
query1df.show()

# Instructions for python script execution
```console
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py {insert flags depending on query}
```
```
    parser.add_argument("-q",   "--query",                              help="enter SQL/cypher query",           type=str)
    parser.add_argument("-u",   "--url",                          help="default: localhost",        type=str)
    parser.add_argument("-p", "--preset",                           help="choose predefined query",   type=str)
    parser.add_argument("-s",   "--save",          help="Save to /results. Add a filename as an argument", type=str)
    parser.add_argument("-d",  "--database",                           help="p=postgres or n=neo4j")
    parser.add_argument("-a", "--args", nargs='+', help="custom arguments such as blocknumber")
```
