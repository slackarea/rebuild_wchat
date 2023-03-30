# rebuild_wchat
Rebuild exported WhatsApp chat from _chat.txt file

## Getting Started

...
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.
See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Python3
```

### Installing

A step by step series of examples that tell you how to get a development env running

```
pip install -r requirements.txt
```

...
## Docker
This repository contains the Dockerfile and instructions for building and running the app using Docker.
### Prerequisites
You'll need to have Docker installed on your system. If you don't have it already, you can download and install Docker from the [https://www.docker.com/get-started/] (official website).

### Build the Docker Image
Use the following command in the root directory of the repository:

```
docker build --pull --rm -f "Dockerfile" -t rebuildwchat:latest "."
```
### Run the app with Docker Compose
Use the following command:

```
docker compose -f "docker-compose.yml" up -d --build
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details about the process for submitting pull requests to us and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on our code of conduct. 

## Versioning

cooming soon

## Authors

* **Vincenzo Ingrosso** - *Initial work* - [slackarea](https://github.com/slackarea)
* **Giampiero Giacalone** - *Initial work* - [gi4mp](https://github.com/gi4mp)
* **Vito Monteleone** - *Initial work* - [Monteleone](https://github.com/Monteleone)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

