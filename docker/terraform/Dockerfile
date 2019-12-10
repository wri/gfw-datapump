FROM hashicorp/terraform:0.12.13

RUN \
    apk add --no-cache \
        bash \
        make \
        python3 \
        zip \
    && pip3 install awscli

COPY infra /usr/local/bin/
COPY select_workspace /usr/local/bin/
COPY delete_workspace /usr/local/bin/