FROM ubuntu:20.04
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create and move to work directory
RUN mkdir -p /srv/worker
WORKDIR /srv/worker

# Install needed packages
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN apt-get -y install default-jre

# Install needed python modules
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copy scripts and packages
RUN mkdir packages

# Run worker
ENTRYPOINT [ "python3", "local_worker.py" ]