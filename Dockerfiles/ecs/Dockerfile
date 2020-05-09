FROM laurents/uvicorn-gunicorn-fastapi:python3.7-slim
# Ref https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker/issues/15
# Cuts image size by 50%
# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

COPY README.md /app/README.md
COPY titiler/ /app/titiler/
COPY setup.py /app/setup.py

RUN pip install -e /app/. --no-cache-dir
