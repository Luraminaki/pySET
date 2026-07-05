FROM node:lts-alpine AS buildfront

COPY ./flask /flask

WORKDIR /flask

RUN npm install
RUN npm run generate


FROM python:3.12-bullseye
ENV PYTHONUNBUFFERED 1

# server_app.py serves the app from flask/dist (see pyset/server_app.py); copy .output/public's
# real contents straight into it rather than .output/server (Nitro's unused Node server bundle).
COPY --from=buildfront ./flask/.output/public /flask/dist/
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