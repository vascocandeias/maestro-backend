# MAESTRO back-end
This repo contains the on-prem implementation of [MAESTRO](https://vascocandeias.github.io/maestro), a website for multivariate time series analysis using dynamic Bayesian networks. The local architecture is depicted bellow.

<p align="center">
  <img src="Local.png"/>
</p>

The publicly available website was deployed in AWS, and the relevant code is available [here](https://github.com/vascocandeias/maestro-cloud). You can also find the front-end code [here](https://github.com/vascocandeias/maestro), which can be modified and [added to this back-end](#changing-the-front-end). 

## Getting Started

### Prerequisites
This project only needs Docker installed, which can be done [here](https://docs.docker.com/get-docker).

### Installation
1. If Docker is not running, start it.
2. [Download](https://api.github.com/repos/vascocandeias/maestro-backend/zipball) and unzip the source.
3. Change the environment variables in ```docker-compose.yml```.
4. Start the containers:
   * When using Windows, you may double-click the ```maestro.bat``` file.  
   or
   * Open the terminal inside the project's directory and run ```docker-compose up```.
5. Access the website at [http://localhost](http://localhost). For other devices on the same network, you must replace ```localhost``` with the server's IP address.

### Other useful commands
#### Shut down
Just press ```Ctrl+C```.

#### Scale out the workers
If you want to change the number of workers to ```x```, open a new terminal in the project root directory and run ```docker-compose up -d --scale worker=x```.

### Adding more packages
To add more packages, you must copy the program to ```worker/packages```. Furthermore, you must create a json file in the same directory with the following syntax:

```json
{
	"cmd": [
		"java",
		"-jar",
		"packages/sdtDBN.jar",
		"-pm",
		"-d",
		"-toFile",
		"dbn.ser"
	],
	"params": {
		"-b": 1,
		"-m": 1,
		"-ns": false,
		"-s": "mdl",
		"-p": 1,
		"-sp": false
	},
	"inputFiles": {
		"-i": "file to be used for network learning",
		"-is": "static features to be used for network learning",
		"-mA_dynPast": "dynamic nodes from t'<t that must be parents of each Xi[t]",
		"-mA_dynSame": "dynamic nodes from t that must be parents of each Xi[t]",
		"-mA_static": "static nodes that must be parents of each Xi[t]",
		"-mNotA_dynPast": "dynamic nodes from t'<t that cannot be parents of each Xi[t]",
		"-mNotA_dynSame": "dynamic nodes from t that cannot be parents of each Xi[t]",
		"-mNotA_static": "static nodes that cannot be parents of each Xi[t]"
	},
	"outputFiles": {
		"dbn.txt": {},
		"dbn.json": {},
		"dbn.ser": {
			"table": "networks"
		}
	}
}
```

If the new packages were written in either Java, you are done. The same goes for Python if no extra libraries are needed.

Otherwise, if you use Python but your code requires any other library, add it to ```worker/requirements.txt```. When using languages that would require extra system dependencies, you must add a command to the ```worker/Dockerfile``` that installs them. In both of these scenarios, with the containers already running, execute ```docker-compose up -d --no-deps --build --scale worker=x worker```, where ```x``` is the number of workers.

### Changing the front-end
