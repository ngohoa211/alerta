FROM python:3.6-stretch
ENV PYTHONUNBUFFERED 1

LABEL maintainer="hoanq13@viettel.com.vn"

ARG BUILD_DATE=now
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.url="https://alerta.io" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0.0-rc.1"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nano \
    gettext-base \
    libffi-dev \
    libldap2-dev \
    libpq-dev \
    libsasl2-dev \
    mongodb-clients \
    nginx-light \
    postgresql-client \
    python3-dev \
    supervisor \
    wget && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip3 install -r /app/requirements.txt
#RUN pip install --no-cache-dir virtualenv && \
#    virtualenv --python=python3 /venv && \
#    /venv/bin/pip install -r /app/requirements.txt
#ENV PATH $PATH:/venv/bin
RUN mkdir source

COPY python-alerta-client source/python-alerta-client
RUN cd source/python-alerta-client && pip3 install -r requirements.txt && python3 setup.py install

COPY alerta source/alerta
RUN cd source/alerta && pip3 install -r requirements.txt && python3 setup.py install

COPY alerta-contrib source/alerta-contrib
COPY install-plugins.sh /app/install-plugins.sh
COPY plugins.txt /app/plugins.txt
RUN chmod +x /app/install-plugins.sh
RUN /app/install-plugins.sh

COPY alerta-webui/alerta-webui.v7.4.1.tar.gz /tmp/webui.tar.gz
RUN tar zxvf /tmp/webui.tar.gz -C /tmp && \
    mv /tmp/dist /web
COPY config.json.template /web/config.json.template

COPY wsgi.py /app/wsgi.py
COPY uwsgi.ini /app/uwsgi.ini
COPY nginx.conf /app/nginx.conf

RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stdout /var/log/nginx/error.log
RUN chgrp -R 0 /app /web && \
    chmod -R g=u /app /web && \
    useradd -u 1001 -g 0 alerta

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
COPY supervisord.conf /app/supervisord.conf

USER 1001

ENV ALERTA_SVR_CONF_FILE /app/alertad.conf
ENV ALERTA_CONF_FILE /app/alerta.conf
ENV ALERTA_WEB_CONF_FILE /web/config.json
ENV PATH $PATH:/usr/local/bin

ENV BASE_URL /api
ENV HEARTBEAT_SEVERITY major


ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 8080
CMD ["supervisord", "-c", "/app/supervisord.conf"]
