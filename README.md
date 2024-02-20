# SET

Fun project where I could cram in some of the knowledge I gained from coding in VUE-2 and VUE-3 (With NUXT) and Python-3. Feel free to check the [game rules](https://en.wikipedia.org/wiki/Set_(card_game)#Games) before playing... In its current state, the game is meant to be played on a single screen, and you will need to know how to use the terminal command prompt in order to build / install / run this game.

## VERSIONS

- 0.1.0-alpha: First release
- 0.2.0-alpha: Multiple Game Sessions

## TABLE OF CONTENT

<!-- TOC -->

- [SET](#set)
  - [VERSIONS](#versions)
  - [TABLE OF CONTENT](#table-of-content)
  - [TL;DR](#tldr)
  - [INSTALL AND BUILD GUIDE (WebUI - Front)](#install-and-build-guide-webui---front)
  - [INSTALL AND START GUIDE (Server - Back)](#install-and-start-guide-server---back)
  - [DOCKER](#docker)
  - [POSSIBLE FUTURE UPDATES](#possible-future-updates)

<!-- /TOC -->

## TL;DR

"I don't want to install anything or read anything, just make it quick and easy please." I hear you say? Sure, just click [here](https://pyset.onrender.com/) and have fun. 

## INSTALL AND BUILD GUIDE (WebUI - Front)

If you have [Docker](https://www.docker.com/) or [Rancher](https://www.rancher.com/) installed, you can skip to [this section](#docker).
If you only want to run the project on your own machine, just skip to [this section](#install-and-start-guide-server---back).
If you want to build and run the project from scratch on your own machine, well, there's a bit of reading, and it starts now.

- Clone, or download + extract [this project](https://github.com/Luraminaki/pySET/archive/refs/heads/main.zip)
- For `NodeJS` installation, consult the following [link](https://nodejs.org/en/download)
- For `Yarn` installation, consult the following [link](https://classic.yarnpkg.com/lang/en/docs/install/)

Once done, open a new terminal in the directory `pySET` and type the following commands to build the WebUI.

```sh
cd pySET/flask
yarn install
yarn generate
```

## INSTALL AND START GUIDE (Server - Back)

In this section, I will assume that you either followed the building instructions above, or downloaded and extracted [the latest release](https://github.com/Luraminaki/pySET/releases).

- For `Python 3` installation, consult the following [link](https://www.python.org/downloads/)

Once done, open a new terminal in the directory `pySET` and type the following command to create the python virtual environment.

```sh
python -m venv .venv
```

In the same terminal, activate the `.venv` previously created as follow, or as shown in [HowTo](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments), and install the project's dependencies.

- **Windows**

```sh
.venv\Scripts\activate
pip install -U -r requirements.txt
```

- **Unix** or **MacOS**

```sh
source .venv/bin/activate
pip install -U -r requirements.txt
```

Once done, you can run the project with either

```sh
python3 server_app.py -c config.json
```

or

```sh
gunicorn -c gunicorn/dev_app.py
```

You can now open your favorite web browser and [start-the-game](http://localhost/)

## DOCKER

I wrote a `Dockerfile` as a training exercise and for those that want something that "just works". (Though, you have to know how [Docker](https://www.docker.com/) or [Rancher](https://www.rancher.com/) works beforehand...)

```sh
cd pySET
docker build -t pyset:0.2 .
docker run -d -p 10000:10000 pyset:0.2
```

## POSSIBLE FUTURE UPDATES

- "AI" player(s)
- Handle multiple clients (different screens)
- Testing scripts
