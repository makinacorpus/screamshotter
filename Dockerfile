FROM ubuntu:bionic
MAINTAINER Makina Corpus "contact@geotrek.fr"

RUN apt-get update && apt-get upgrade -qq -y
RUN apt-get install -y -qq libfreetype6 fontconfig wget unzip python-pip python-virtualenv
RUN apt-get autoclean && apt-get clean all

#
#  PhantomJS
#...
RUN rm -rf /opt/*phantomjs*/
RUN wget --quiet https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2 -O /opt/phantomjs.tar.bz2
RUN tar -jxvf /opt/phantomjs.tar.bz2 -C /opt/
RUN rm /opt/phantomjs.tar.bz2
RUN ln -sf /opt/*phantomjs*/bin/phantomjs /usr/bin/

#
#  CasperJS
#...
RUN rm -rf /opt/*casperjs*/
RUN wget --quiet https://github.com/n1k0/casperjs/archive/1.1-beta3.zip -O /opt/casperjs.zip
RUN unzip -o /opt/casperjs.zip -d /opt/ > /dev/null
RUN rm /opt/casperjs.zip
RUN ln -sf /opt/*casperjs*/bin/casperjs /usr/bin/

#
#  Screamshotter
#...
ADD . /opt/apps/screamshotter
WORKDIR /opt/apps/screamshotter
RUN  make install deploy
RUN /opt/apps/screamshotter/bin/pip install Pillow

RUN /opt/apps/screamshotter/bin/pip install uwsgi
ADD .docker/run.sh /usr/local/bin/run

#
#  Run !
#...
EXPOSE 8000
CMD ["/bin/sh", "-e", "/usr/local/bin/run"]