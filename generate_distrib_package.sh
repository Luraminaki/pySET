#! /usr/bin/env bash

REPO="git@github.com:Luraminaki/pySET.git"
BRANCH_OR_TAG="main"
INSTALL_DIR="pySET"
DEST="pySET"

echo "Generating ${DEST} from ${BRANCH_OR_TAG} from repository ${REPO}"

git fetch --all -p
git checkout ${BRANCH_OR_TAG}
git pull

cd flask
npm install
npm run generate
cd ..

rm -f ${DEST}.zip
# `npm run generate` writes the built site straight to flask/dist (see nuxt.config.ts's
# nitro.output.publicDir and pyset/server_app.py, which serves the app from flask/dist) -- a
# real, populated directory, not a symlink, so this just zips it directly.
zip -qr ${DEST}.zip ./{README.md,INSTALL.md,pyproject.toml,config.json,.env.example,pyset/*,gunicorn/*.py} ./flask/dist/*
echo "Done !"
