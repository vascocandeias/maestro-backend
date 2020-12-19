# MAESTRO back-end
This repo contains the on-prem implementation of [MAESTRO](https://vascocandeias.github.io/maestro), a website for multivariate time series analysis using dynamic Bayesian networks which can be [deployed on-premises](#getting-started). The local architecture is depicted bellow.

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
You may also add your custom methods to this website to take advantage of its architecture and front-end without having to build an entire system. Read further to know how to upload the program's code, interface and template.

#### Code and interface
To add more packages, you must copy the program to ```worker/packages```. Furthermore, you must create an interface JSON file in the same directory with a specific scheme. The following file is the interface of the ```eqw``` method, ```eqw.json```:

```json
{
	"cmd": [
		"python3",
		"packages/time_series_tools.py",
		"eqf"
	],
	"params": {
		"-n": 2,
		"-d": ""
	},
	"inputFiles": {
		"-i": "continuous multivariate time series file"
	},
	"outputFiles": {
		"discrete.csv": {
			"table": "datasets",
			"discrete": true,
			"original": {
				"-i": {
					"table": "datasets",
					"attributes": [
						"missing"
					]
				}
			}
		}
	}
}
```
The fields are the following:
  * ```cmd``` (strings list) - The base command to execute the package as a list of strings, to which the remaining parameters will be added.
  * ```params``` (dict) - A dictionary containing the flags accepted by the package, as key-value pairs, used to filter the request. When the value is a Boolean, the flag takes no value, and should simply be either present or absent. Otherwise, the value is either the default value or a representation of the type of input but will not affect building the command.
  * ```inputFiles``` (dict) - A key-value representation of the accepted input files, where the value is a description the file used for the corresponding key.
  * ```outputFiles``` (dict) - A dictionary containing as its keys the output files, which should be saved in the database. When these values have no metadata, the value is ```{}```. Otherwise, the value will be a dictionary with a ```table``` key, containing the name of the table that should hold the metadata, followed by this information represented as key-value pairs and, finally, it might even have an ```original``` field, reserved for whenever the result inherits metadata from one of the ```inputFiles```. To accommodate these unknowns, this attribute consists of key-value pairs where the keys must also be present in ```inputFiles``` and the values are dictionaries consisting of the following attributes:
    * ```table``` (string) - The table containing the original file.
    * ```attributes``` (string list) - A list with the metadata attributes to copy from the original file.
    
#### Template

You should also provide a template for your method's front-end input form. This file should be placed inside ```database/methods``` and look something like the following, which is the template for the ```learnsdtDBN```, ```learnsdtDBN.json```:

```json
{
    "checkboxes": {
        "-ns": "Learn non-stationary network",
        "-sp": "Force intra-slice connectivity to be a tree"
    },
    "fields": {
        "-b": {
            "description": "Number of static parents",
            "value": 2
        },
        "-m": {
            "description": "Markov lag",
            "value": 1
        },
        "-p": {
            "description": "Number of parents",
            "value": 1
        }
    },
    "files": {
		"-is": "Static features file",
		"-mA_dynPast": "Mandatory inter-slice relations",
		"-mA_dynSame": "Mandatory intra-slice relations",
		"-mA_static": "Mandatory static relations",
		"-mNotA_dynPast": "Forbidden inter-slice relations",
		"-mNotA_dynSame": "Forbidden intra-slice relations",
		"-mNotA_static": "Forbidden static relations"
    },
    "mainFile": {
        "name": "-i",
        "metadata": {
            "discrete": true,
            "missing": false
        }
    },
    "method": "learnsdtDBN",
    "options": {
        "-s": {
            "description": "Scoring function",
            "values": [
                "mdl",
                "ll"
            ]
        }
    }
}
```
The fields have the following meanings:
  * ```checkboxes``` (dict) - Every Boolean parameter as key-value pairs where the key is the parameter's name and the value is its description.
  * ```fields``` (dict) - Key-value pairs representing text or number input fields where the keys are the parameters' names and the values are dictionaries containing their descriptions and default values.
  * ```files``` (dict) - Every input file (except the main one) represented as key-value pairs, where the key is the file's input name and the value is its description.
  * ```mainFile``` (dict) - A dictionary containing the name of the main input file and its metadata (for example, if it must be discrete or have missing values).
  * ```method``` (string) - The method's name.
  * ```options``` (dict) - Key-value pairs with the parameters that have multiple options, where the keys are their names and the values have the their descriptions and a list of the possible values.

#### Deployment
If the new packages were written in Java, you are done. The same goes for Python if no extra libraries are needed.

Otherwise, if you use Python but your code requires any other library, add it to ```worker/requirements.txt```. When using languages that would require extra system dependencies, you must add a command to the ```worker/Dockerfile``` that installs them. In both of these scenarios, with the containers already running, execute ```docker-compose up -d --no-deps --build --scale worker=x worker```, where ```x``` is the number of workers.

### Changing the front-end
