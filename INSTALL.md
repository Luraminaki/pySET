# INSTALL

This guide covers building the frontend, installing the backend, and running the project, either
natively or via Docker/Rancher.

## TABLE OF CONTENT

<!-- TOC -->

- [INSTALL](#install)
  - [TABLE OF CONTENT](#table-of-content)
  - [PREREQUISITES](#prerequisites)
    - [Node.js](#nodejs)
    - [Python 3](#python-3)
  - [BUILD GUIDE (WebUI - Front)](#build-guide-webui---front)
  - [INSTALL AND START GUIDE (Server - Back)](#install-and-start-guide-server---back)
  - [DOCKER](#docker)

<!-- /TOC -->

## PREREQUISITES

### Node.js

- **Debian / Ubuntu**

```sh
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

- **Arch Linux**

```sh
sudo pacman -Syu nodejs npm
```

- **Windows**

```powershell
winget install OpenJS.NodeJS.LTS
```

Alternatively, download the installer from [nodejs.org](https://nodejs.org/en/download).

### Python 3

This project targets **Python 3.12+**.

- **Debian / Ubuntu**

```sh
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
```

- **Arch Linux**

```sh
sudo pacman -Syu python python-pip
```

- **Windows**

```powershell
winget install Python.Python.3.12
```

Alternatively, download the installer from [python.org](https://www.python.org/downloads/).

## BUILD GUIDE (WebUI - Front)

If you have [Docker](https://www.docker.com/) or [Rancher](https://www.rancher.com/) installed, you
can skip to [this section](#docker). If you only want to run the project on your own machine without
rebuilding the frontend, skip to [this section](#install-and-start-guide-server---back).

- Clone, or download + extract [this project](https://github.com/Luraminaki/pySET/archive/refs/heads/main.zip)
- Install Node.js as described [above](#nodejs)

Once done, open a new terminal in the directory `pySET` and type the following commands to build the WebUI.

```sh
cd pySET/flask
npm install
npm run generate
```

## INSTALL AND START GUIDE (Server - Back)

In this section, it is assumed that you either followed the building instructions above, or
downloaded and extracted [the latest release](https://github.com/Luraminaki/pySET/releases).

- Install Python 3 as described [above](#python-3)

Once done, open a new terminal in the directory `pySET` and type the following command to create the
Python virtual environment.

```sh
python -m venv .venv
```

In the same terminal, activate the `.venv` previously created as follow, or as shown in
[HowTo](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments), and install the
project (this reads `pyproject.toml`, no `requirements.txt` involved anymore).

- **Windows**

```powershell
.venv\Scripts\activate
pip install -U .
```

- **Unix** or **MacOS**

```sh
source .venv/bin/activate
pip install -U .
```

If you intend to work on the Python code itself, install it in editable mode with the linting/type-checking
tools instead:

```sh
pip install -U -e ".[dev]"
```

This pulls in [Ruff](https://docs.astral.sh/ruff/) (linter + formatter + import sorting),
[mypy](https://mypy-lang.org/) (static type checking) and [pytest](https://docs.pytest.org/) (test
suite, in `tests/`), which can then be run from the repo root:

```sh
ruff check .
ruff format .
mypy .
pytest
```

These are the exact same checks the `Python CI` GitHub Actions workflow
(`.github/workflows/python-ci.yml`) runs on every push/PR.

The admin endpoint that wipes every running game session (`delete_running_games`) is protected by a
secret. `config.json` ships with an empty `secret` (which disables the endpoint entirely), so if you
want to use it, set `PYSET_ADMIN_SECRET` instead of editing `config.json` - it always takes
precedence and keeps the real value out of a file that gets committed. Either a real environment
variable or a `.env` file works (see `.env.example`); the `.env` file is read from the directory
you run the project from and is gitignored.

- **`.env` file** (works the same on every OS)

```sh
cp .env.example .env
# then edit .env and set PYSET_ADMIN_SECRET=some-long-random-value
```

- **Windows** (environment variable instead)

```powershell
$env:PYSET_ADMIN_SECRET = "some-long-random-value"
```

- **Unix** or **MacOS** (environment variable instead)

```sh
export PYSET_ADMIN_SECRET="some-long-random-value"
```

Once done, you can run the project with either

```sh
python -m pyset.server_app -c config.json
```

or

```sh
gunicorn -c gunicorn/dev_app.py
```

You can now open your favorite web browser and [start-the-game](http://localhost:10000)

## DOCKER

I wrote a `Dockerfile` as a training exercise and for those that want something that "just works".
(Though, you have to know how [Docker](https://www.docker.com/) or [Rancher](https://www.rancher.com/)
works beforehand...)

```sh
cd pySET
docker build -t pyset:0.2 .
docker run -d -p 10000:10000 -e PYSET_ADMIN_SECRET="some-long-random-value" pyset:0.2
```
