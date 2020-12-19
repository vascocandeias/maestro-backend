# MAESTRO back-end
This repo contains the on-prem implementation of [MAESTRO](https://vascocandeias.github.io/maestro), a website for multivariate time series analysis using dynamic Bayesian networks. 

## Getting Started


<p align="center">
  <img src="Local.png"/>
</p>


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
5. Access the website at [http://localhost](http://localhost). For other devices on the same network, you may replace ```localhost``` with the server's IP address.
