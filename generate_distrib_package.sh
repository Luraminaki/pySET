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
yarn install
yarn generate
cd..

rm -f ${DEST}.zip
zip -qr ${DEST}.zip ./{README.md,*.py,requirements.txt,config.json,modules/*,gunicorn/*.py} ./flask/.output/*
echo "Done !"
