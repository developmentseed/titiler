FROM tiangolo/uvicorn-gunicorn:python3.8

# Ensure root certificates are always updated at evey container build
# and curl is using the latest version of them
RUN mkdir /usr/local/share/ca-certificates/cacert.org
RUN cd /usr/local/share/ca-certificates/cacert.org && curl -k -O https://www.cacert.org/certs/root.crt 
RUN cd /usr/local/share/ca-certificates/cacert.org && curl -k -O https://www.cacert.org/certs/class3.crt
RUN update-ca-certificates
ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

COPY src/titiler/ /tmp/titiler/

RUN pip install /tmp/titiler/core /tmp/titiler/mosaic /tmp/titiler/application --no-cache-dir

RUN rm -rf /tmp/titiler

ENV MODULE_NAME titiler.application.main
ENV VARIABLE_NAME app
