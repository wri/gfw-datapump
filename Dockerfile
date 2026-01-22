FROM hashicorp/terraform:0.13.3

RUN apk update
RUN apk add --update --no-cache docker
RUN apk --no-cache add openjdk11 --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community

ENV MAVEN_VERSION="3.5.4"
ENV MAVEN_HOME="/usr/lib/mvn"
ENV PATH=${MAVEN_HOME}/bin:${PATH}

RUN wget http://archive.apache.org/dist/maven/maven-3/$MAVEN_VERSION/binaries/apache-maven-$MAVEN_VERSION-bin.tar.gz -O - | tar -zxvf - && \
  mv apache-maven-$MAVEN_VERSION /usr/lib/mvn

RUN apk add --no-cache --upgrade curl bash gcc libc-dev geos-dev musl-dev linux-headers g++ git libffi-dev

ENV PYTHON_VERSION="3.9" \
    USR_LOCAL_BIN=/usr/local/bin \
    UV_VERSION="0.9.26" \
    VENV_DIR=/app/.venv \
    PATH=${USR_LOCAL_BIN}:${PATH} \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=${VENV_DIR} \
    UV_UNMANAGED_INSTALL=${USR_LOCAL_BIN} \
    PYTHONUNBUFFERED=1

RUN curl -LsSf https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh | sh && \
    uv venv ${VENV_DIR} --python ${PYTHON_VERSION} --seed

ENV PATH=${VENV_DIR}/bin:${PATH}

COPY ./src /src

COPY pyproject.toml /_lock/
COPY uv.lock /_lock/

RUN cd /_lock && \
    source ${VENV_DIR}/bin/activate && \
    uv sync --locked && \
    uv pip install /src
