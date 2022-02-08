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
```./polkadot --name "Your Node's Name"```

You should either daemonize it via systemctl/supervisorctl or use the screen command to detach it from the current terminal