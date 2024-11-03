FROM openresty/openresty:1.25.3.1-jammy
STOPSIGNAL SIGQUIT
# Set the locale environment variables
ENV LC_CTYPE=C
ENV LC_COLLATE=C
ENV LC_MESSAGES=C
ENV LC_NUMERIC=C
ENV LC_TIME=C
ARG ARCH
# Install base dependencies
RUN set -x \
&& apt update
RUN set -x \
&& apt install -y \
wget \
procps \
vim \
jq \
supervisor


RUN wget -q https://github.com/mikefarah/yq/releases/download/v4.44.3/yq_linux_${ARCH} -O /usr/bin/yq && chmod +x /usr/bin/yq

ENV DOCKERIZE_VERSION v0.8.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-$ARCH-$DOCKERIZE_VERSION.tar.gz \
&& tar -C /usr/local/bin -xzvf dockerize-linux-$ARCH-$DOCKERIZE_VERSION.tar.gz \
&& rm dockerize-linux-$ARCH-$DOCKERIZE_VERSION.tar.gz


COPY templates/ /templates
COPY scripts/ /scripts/
COPY files/common.conf /etc/nginx/common.conf

RUN mkdir -p /etc/nginx/ssl/
RUN mkdir -p /projects/
RUN mkdir -p /commands/


ENTRYPOINT ["/scripts/entrypoint.sh"]

EXPOSE 80 443 81
