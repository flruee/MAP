# Setup

## Setup Polkadot node
[Web instructions](https://wiki.polkadot.network/docs/maintain-sync)  
  
Create directory and switch to it  
```mkdir polkadot```  
```cd polkadot```

Download binaries  
```curl -sL https://github.com/paritytech/polkadot/releases/download/*VERSION*/polkadot -o polkadot```  
Where version is replaced by latest version (v0.9.16, as of 08.02.2022)

Make it executable  
```sudo chmod +x polkadot```

Run it  
```./polkadot --name "polkaDotMapNode" --rpc-cors all --pruning=archive --wasm-execution Compiled"```

You should either daemonize it via systemctl/supervisorctl or use the screen command to detach it from the current terminal.  

## Setup Kafka
[Web instructions](https://kafka.apache.org/quickstart)  
Download kafka (maybe change version) 
```wget https://dlcdn.apache.org/kafka/3.1.0/kafka_2.13-3.1.0.tgz```

unzip it  
```tar -xzf kafka_2.13-3.1.0.tgz```  
```cd kafka_2.13-3.1.0```  
  
start the services  
  ```bin/zookeeper-server-start.sh config/zookeeper.properties```

In another terminal  
```bin/kafka-server-start.sh config/server.properties```

Create a topic  
```bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic polkadotBlockData```

Read topic  
```bin/kafka-console-consumer.sh --topic polkadotBlockData --from-beginning --bootstrap-server localhost:9092```





## Setup producer/preprocessor/spark module
See README in their respective folders.
