FROM node:lts-alpine AS buildfront

COPY ./flask /flask

WORKDIR /flask

RUN npm install
RUN npm run generate


FROM python:3.12-bullseye
ENV PYTHONUNBUFFERED 1

# `npm run generate` writes the built site straight to flask/dist (see nuxt.config.ts's
# nitro.output.publicDir and pyset/server_app.py, which serves the app from flask/dist).
COPY --from=buildfront ./flask/dist /flask/dist/
COPY ./gunicorn /gunicorn/
COPY ./pyset /pyset/
COPY config.json ./
COPY README.md ./
COPY pyproject.toml ./

RUN python3 -m venv .venv
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install -U .

CMD [ ".venv/bin/python3", "-m", "pyset.server_app", "-c", "config.json" ]

EXPOSE 10000