FROM tiangolo/uvicorn-gunicorn:python3.8

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt


COPY titiler/ /tmp/titiler/

# rasterio 1.2.0 wheels are built using GDAL 3.2 and PROJ 7 which we found having a
# performance downgrade: https://github.com/developmentseed/titiler/discussions/216
RUN pip install /tmp/titiler/core /tmp/titiler/mosaic /tmp/titiler/application rasterio==1.1.8 --no-cache-dir

RUN rm -rf /tmp/titiler

ENV MODULE_NAME titiler.application.main
ENV VARIABLE_NAME app
