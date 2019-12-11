FROM lambci/lambda:build-python3.7

WORKDIR /var/task
ENV WORKDIR /var/task

WORKDIR $WORKDIR
RUN mkdir -p python

# Make the dir and to install all packages into packages/
COPY docker/shapely_pyyaml/.lambdaignore .

# installing dependencies to build package
RUN pip install PyYAML~=5.2 shapely~=1.6.4.post2 -t python

#Precompile all python packages and remove .py files
RUN python -m compileall .
RUN find python/ -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-37//'); cp $f $n; done;
RUN find python/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find python/ -type f -a -name '*.py' -print0 | xargs -0 rm -f

# Compress all source codes expect files listed in .lambdaignore
RUN cat .lambdaignore | xargs zip -9qyr layer.zip python -x

CMD ["/bin/bash"]