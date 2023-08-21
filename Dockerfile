FROM hashicorp/terraform:0.13.7

ENV PYTHONUNBUFFERED=1
RUN apk update
RUN apk add --update --no-cache docker
RUN apk --no-cache add openjdk11 --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community

ENV MAVEN_VERSION 3.5.4
ENV MAVEN_HOME /usr/lib/mvn
ENV PATH $MAVEN_HOME/bin:$PATH

RUN wget http://archive.apache.org/dist/maven/maven-3/$MAVEN_VERSION/binaries/apache-maven-$MAVEN_VERSION-bin.tar.gz -O - | tar -zxvf - && \
  mv apache-maven-$MAVEN_VERSION /usr/lib/mvn

RUN apk add --no-cache --upgrade bash gcc libc-dev python3 python3-dev geos-dev musl-dev linux-headers g++ git && \
RUN ln -sf python3 /usr/bin/python && \
  python3 -m ensurepip && \
  pip3 install --no-cache-dir --upgrade pip setuptools pytest pytest-cov boto3 shapely

RUN mkdir datapump
COPY ./src src
RUN pip3 install ./src