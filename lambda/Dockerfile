FROM lambci/lambda:build-python3.7

WORKDIR /tmp

# We install titiler and mangum
RUN pip install git+https://github.com/developmentseed/titiler.git mangum -t /var/task --no-binary numpy

# Reduce package size and remove useless files
RUN cd /var/task && find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN cd /var/task && find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN cd /var/task && find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN find /var/task -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN rm -rdf /var/task/numpy/doc/
RUN rm -rdf /var/task/stack

RUN cd /var/task && zip -r9q /tmp/package.zip *

COPY handler.py handler.py
RUN zip -r9q /tmp/package.zip handler.py