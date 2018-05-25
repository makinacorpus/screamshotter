FROM ubuntu:bionic
MAINTAINER Makina Corpus "contact@makina-corpus.com"

RUN apt-get update && apt-get install -y -qq libfreetype6 fontconfig wget unzip python-pip python-virtualenv && \
    apt-get autoclean && apt-get clean all && rm -rf /var/pt/lists/*

# PhantomJS
RUN rm -rf /opt/*phantomjs*/ && wget --quiet https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2 -O /opt/phantomjs.tar.bz2 &&\
    tar -jxvf /opt/phantomjs.tar.bz2 -C /opt/ && rm /opt/phantomjs.tar.bz2 && ln -sf /opt/*phantomjs*/bin/phantomjs /usr/bin/

# CasperJS
RUN rm -rf /opt/*casperjs*/ && wget --quiet https://github.com/n1k0/casperjs/archive/1.1-beta3.zip -O /opt/casperjs.zip &&\
    unzip -o /opt/casperjs.zip -d /opt/ > /dev/null && \
    rm /opt/casperjs.zip && ln -sf /opt/*casperjs*/bin/casperjs /usr/bin/

ADD .docker/run.sh /usr/local/bin/run

#
#  Screamshotter
#...
ADD . /opt/apps/screamshotter
WORKDIR /opt/apps/screamshotter

# add user django
RUN useradd -ms /bin/bash django && chown -R django:django /opt/apps/screamshotter
USER django

RUN  make install deploy
RUN /opt/apps/screamshotter/bin/pip install Pillow gunicorn

#
#  Run !
#...
EXPOSE 8000
CMD ["/bin/sh", "-e", "/usr/local/bin/run"]