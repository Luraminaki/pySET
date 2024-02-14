# SET

Fun project where I could cram in some of the knowledge I gained from coding in VUE-2 and VUE-3 (With NUXT) and Python-3. Feel free to check the [game rules](https://en.wikipedia.org/wiki/Set_(card_game)#Games) before playing... In its current state, the game is meant to be played on a single screen.

## INSTALL AND BUILD GUIDE

- Clone or download + extract this project

- For NodeJS, consult the following [link](https://nodejs.org/en/download)
- For Yarn, consult the following [link](https://classic.yarnpkg.com/lang/en/docs/install/#debian-stable)
- For Python, consult the following [link](https://www.python.org/downloads/)

```sh
cd pySET
python -m venv .venv

.venv/bin/pip install -U -r requirements.txt

cd flask
yarn install
yarn generate
```

## START GUIDE

Open a new terminal in the directory `pySET` and activate the `.venv` previously created as follow, or as shown in [HowTo](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments)

- Windows

```sh
.venv\Scripts\activate
```

- Unix or MacOS

```sh
source .venv/bin/activate
```

Once activated, you can run the project with either

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

## FUTURE UPDATES

- Improve GUI (Player score particularly)
- Handle multiple clients
- "AI" player(s)
- Testing scripts
