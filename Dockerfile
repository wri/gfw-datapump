FROM --platform=linux/amd64 ubuntu:noble

ENV PYTHON_VERSION="3.9" \
    USR_LOCAL_BIN=/usr/local/bin \
    UV_VERSION="0.9.26" \
    VENV_DIR=/app/.venv \
    PATH=${USR_LOCAL_BIN}:${PATH} \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=${VENV_DIR} \
    UV_UNMANAGED_INSTALL=/usr/local/bin

RUN apt-get -qy update && \
    apt-get install -qy --no-install-recommends --no-install-suggests \
      apt-transport-https \
      ca-certificates \
      curl \
      docker.io \
      git \
      gnupg \
      jq \
      libc-dev \
      libgeos-dev \
      libpq-dev \
      libffi-dev \
      lsb-release \
      make \
      openjdk-11-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists && \
    rm -rf /var/cache/apt

ENV MAVEN_VERSION="3.5.4"
ENV MAVEN_HOME="/usr/lib/mvn"
RUN curl https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz | tar -zxvf - && \
    mv apache-maven-$MAVEN_VERSION ${MAVEN_HOME}
ENV PATH=${MAVEN_HOME}/bin:${PATH}

RUN echo "Install terraform" && \
    curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor > /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && \
    apt-get install -qy --no-install-recommends terraform=0.13.3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists && \
    rm -rf /var/cache/apt

# Copy over the source
COPY ./src /src
RUN mkdir -p /app
COPY pyproject.toml uv.lock /app/

# Create a virtual environment with uv and install deps
RUN curl -LsSf https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh | sh && \
    uv venv /app/.venv --python ${PYTHON_VERSION} --seed && \
    . ${VENV_DIR}/bin/activate && \
    cd /app && \
    uv sync --locked && \
    uv pip install /src