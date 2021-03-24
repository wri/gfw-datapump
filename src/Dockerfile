FROM lambci/lambda:build-python3.7

ENV WORKDIR /opt
WORKDIR $WORKDIR

RUN mkdir -p /opt/python

# Make the dir and to install all packages into packages/
COPY . $WORKDIR

# installing dependencies to build package
RUN pip install . -t python

# change this3094033433223442

#Precompile all python packages and remove .py files
RUN find python/ -type f -name '*.pyc' -print0 | xargs -0 rm -rf
RUN find python/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf

# Compress all source codes expect files listed in .lambdaignore
RUN cat .lambdaignore | xargs zip -9qyr layer.zip python -x

CMD ["/bin/bash"]