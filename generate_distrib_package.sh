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
# flask/dist is a symlink to flask/.output/public created by `npm run generate` (see
# pyset/server_app.py, which serves the app from flask/dist). zip dereferences symlinks by
# default, so this stores the real files under flask/dist/... in the archive -- matching what
# server_app.py expects -- rather than an absolute, machine-specific symlink that would be
# broken on any other machine, or flask/.output/server, which is Nitro's own Node server bundle
# and isn't used by this Flask+gunicorn deployment.
zip -qr ${DEST}.zip ./{README.md,INSTALL.md,pyproject.toml,config.json,.env.example,pyset/*,gunicorn/*.py} ./flask/dist/*
echo "Done !"
