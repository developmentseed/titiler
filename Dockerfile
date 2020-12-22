FROM tiangolo/uvicorn-gunicorn:python3.8

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

COPY README.md /app/README.md
COPY titiler/ /app/titiler/
COPY setup.py /app/setup.py

RUN pip install -e /app/.["server"] --no-cache-dir

ENV MODULE_NAME titiler.main
ENV VARIABLE_NAME app
