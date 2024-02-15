# SET

Fun project where I could cram in some of the knowledge I gained from coding in VUE-2 and VUE-3 (With NUXT) and Python-3. Feel free to check the [game rules](https://en.wikipedia.org/wiki/Set_(card_game)#Games) before playing... In its current state, the game is meant to be played on a single screen, and you will need to know how to use the terminal command prompt in order to build / install / run this game.

## VERSIONS

- 0.1.0-alpha: First release

## TABLE OF CONTENT

<!-- TOC -->

- [SET](#set)
  - [VERSIONS](#versions)
  - [TABLE OF CONTENT](#table-of-content)
  - [INSTALL AND BUILD GUIDE (WebUI - Front)](#install-and-build-guide-webui---front)
  - [INSTALL AND START GUIDE (Server - Back)](#install-and-start-guide-server---back)
  - [DOCKER](#docker)
  - [POSSIBLE FUTURE UPDATES](#possible-future-updates)

<!-- /TOC -->

## INSTALL AND BUILD GUIDE (WebUI - Front)

If you have [Docker](https://www.docker.com/) or [Rancher](https://www.rancher.com/) installed, you can skip directly to [this section](#docker).
If you only want to run the project, you will only need `Python 3` (≥ v3.10), and you can skip directly to [this section](#install-and-start-guide-server---back).
If you plan to build and run the project from scratch, you will need `NodJS` (≥ v21.6), `Yarn` (≥ v1.22), `Python 3` (≥ v3.10).

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

You can now open your favorite web browser and [start-the-game](http://localhost:5000/)

## DOCKER

I wrote a `Dockerfile` as a training exercise and for those that want something that "just works". (Though, you have to know how [Docker](https://www.docker.com/) or [Rancher](https://www.rancher.com/) works beforehand...)

```sh
cd pySET
docker build -t pyset:0.1 .
docker run -d -p 5000:5000 pyset:0.1
```

## POSSIBLE FUTURE UPDATES

- "AI" player(s)
- Handle multiple clients (different screens)
- Handle multiple game session at the same time
- Testing scripts
