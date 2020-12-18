FROM tiangolo/uvicorn-gunicorn:python3.8

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# In order to install rio-tiler, which depends on rio-color we need to install numpy first
# ref: https://github.com/mapbox/rio-color/pull/67
RUN pip install numpy

COPY README.md /app/README.md
COPY titiler/ /app/titiler/
COPY setup.py /app/setup.py

RUN pip install -e /app/.["server"] --no-cache-dir

ENV MODULE_NAME titiler.main
ENV VARIABLE_NAME app
