FROM lambci/lambda:build-python3.7

WORKDIR /var/task
ENV WORKDIR /var/task
ENV LAMBDADIR check_new_areas

# Make the dir and to install all packages into packages/
COPY geotrellis_summary_update "$WORKDIR/geotrellis_summary_update"
COPY lambdas "$WORKDIR/lambdas"
COPY lambdas/$LAMBDADIR/ "$WORKDIR/"
COPY setup.py "$WORKDIR/setup.py"

# installing dependencies to run local tests
RUN pip install -r requirements.txt  \
    && pip install -r requirements-dev.txt \
    && pip install .

# installing dependencies to build package
RUN mkdir -p packages/ \
    && pip install -r requirements.txt -t packages \
    && pip install . -t packages


#Precompile all python packages and remove .py files
RUN python -m compileall .
RUN find packages/ -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-37//'); cp $f $n; done;
RUN find packages/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find packages/ -type f -a -name '*.py' -print0 | xargs -0 rm -f

# Compress all source codes expect files listed in .lambdaignore
RUN mv .lambdaignore $WORKDIR/packages/ \
    && cd $WORKDIR/packages \
    && cat .lambdaignore | xargs zip -9qyr $WORKDIR/lambda.zip . -x
RUN cd $WORKDIR \
    && zip -g lambda.zip lambda_function.py

CMD ["/bin/bash"]