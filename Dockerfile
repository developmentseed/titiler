FROM python:3.8.9-slim-buster

RUN set -ex \
    && mkdir /opt/titiler

WORKDIR /opt/titiler

# Install packages
COPY src/titiler/ /tmp/titiler/

RUN pip install /tmp/titiler/core /tmp/titiler/mosaic /tmp/titiler/application --no-cache-dir --upgrade

RUN rm -rf /tmp/titiler

COPY requirements.txt /opt/titiler
RUN  pip install -r requirements.txt

COPY app.sh /opt/titiler
COPY saildrone_custom_tiler /opt/titiler/saildrone_custom_tiler

# Copy over test data for local development
COPY test_mosaics /opt/titiler/test_mosaics/
COPY sample_data /opt/titiler/sample_data/

#ENV MODULE_NAME titiler.application.main
ENV MODULE_NAME saildrone_custom_tiler.app.main
ENV VARIABLE_NAME app

#ENV TITILER_MOSAIC_BACKEND s3://externaldata.dev.saildrone.com

# expose port
EXPOSE 3000
# Metrics port
EXPOSE 9100

#CMD ["uvicorn titiler.application.main:app"]
CMD ["/opt/titiler/app.sh"]
