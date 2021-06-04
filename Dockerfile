FROM tiangolo/uvicorn-gunicorn:python3.8

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

COPY titiler/ /tmp/titiler/

RUN pip install /tmp/titiler/core /tmp/titiler/mosaic /tmp/titiler/application --no-cache-dir

RUN rm -rf /tmp/titiler

ENV MODULE_NAME titiler.application.main
ENV VARIABLE_NAME app
