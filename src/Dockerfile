FROM public.ecr.aws/lambda/python:3.10

ENV WORKDIR /opt
WORKDIR $WORKDIR

RUN mkdir -p /opt/python

# Make the dir and to install all packages into packages/
COPY . $WORKDIR

# installing dependencies to build package
RUN pip install . -t python

# This next line needs to be changed (just increment the number) in order
# to change the hash of the file and get TF to realize it needs to be
# redeployed. Ticket for a better solution:
# https://gfw.atlassian.net/browse/GTC-1250
# change 4

RUN yum install -y zip geos-devel

# Precompile all python packages and remove .py files
RUN find python/ -type f -name '*.pyc' -print0 | xargs -0 rm -rf
RUN find python/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf

# Compress all source codes except files listed in .lambdaignore
RUN cat .lambdaignore | xargs zip -9qyr layer.zip python -x

CMD ["/bin/bash"]