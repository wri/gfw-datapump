FROM lambci/lambda:build-python3.8

ENV WORKDIR /opt
WORKDIR $WORKDIR

RUN mkdir -p /opt/python

# Make the dir and to install all packages into packages/
COPY . $WORKDIR

# installing dependencies to build package
RUN pip install . -t python

# change 1337

# Precompile all python packages and remove .py files
RUN python -m compileall .
RUN find python/ -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-38//'); cp $f $n; done;
RUN find python/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find python/ -type d -a -name '*.dist-info' -print0 | xargs -0 rm -rf
RUN find python/ -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN find python/ -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN strip -s -R .comment -R .gnu.version python/pydantic/*.so

# Compress all source codes except files listed in .lambdaignore
RUN cat .lambdaignore | xargs zip -9qyr layer.zip python -x

CMD ["/bin/bash"]