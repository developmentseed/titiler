FROM tiangolo/uvicorn-gunicorn:python3.8

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

COPY README.md /app/README.md
COPY titiler/ /app/titiler/
COPY setup.py /app/setup.py

# rasterio 1.2.0 wheels are built using GDAL 3.2 and PROJ 7 which we found having a
# performance downgrade: https://github.com/developmentseed/titiler/discussions/216
RUN pip install -e /app/. rasterio==1.1.8 --no-cache-dir

ENV MODULE_NAME titiler.main
ENV VARIABLE_NAME app
