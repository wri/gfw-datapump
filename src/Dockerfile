# This Dockerfile is used to build the datapump layer for the lambdas.
FROM public.ecr.aws/lambda/python:3.10

ENV WORKDIR /opt
WORKDIR $WORKDIR

RUN mkdir -p /opt/python

# Make the dir and to install all packages into packages/
COPY . $WORKDIR

# Installing dependencies to build package. This implicitly uses setup.py for the
# dependency list.
RUN pip install . -t python

RUN yum install -y zip geos-devel

# Remove any precompiled files and __pycache__ dirs
RUN find python/ -type f -name '*.pyc' -print0 | xargs -0 rm -rf
RUN find python/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf

# Compress all source codes except files listed in .lambdaignore
RUN cat .lambdaignore | xargs zip -9qyr layer.zip python -x

CMD ["/bin/bash"]
