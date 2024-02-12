FROM node:21.6.1-alpine AS buildfront

COPY ./flask /flask

WORKDIR /flask

RUN corepack enable
RUN yarn install
RUN yarn generate


FROM python:3.12.1-bullseye
ENV PYTHONUNBUFFERED 1

COPY --from=buildfront ./flask/.output /flask/.output/
COPY ./gunicorn /gunicorn/
COPY ./modules /modules/
COPY config.json ./
COPY README.md ./
COPY requirements.txt ./
COPY *.py ./

RUN python3 -m venv .venv
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install -U -r requirements.txt

CMD [ ".venv/bin/python3", "server_app.py", "-c", "config.json" ]

EXPOSE 5000