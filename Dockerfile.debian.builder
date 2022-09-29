ARG DISTRO=ubuntu:bionic

FROM ${DISTRO} as base

ARG BUILDID=''

RUN apt-get update -qq -o Acquire::Languages=none && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -yqq lsb-release && \
    if test "$(lsb_release -cs)" = 'focal' ; then \
       env DEBIAN_FRONTEND=noninteractive apt-get install -yqq software-properties-common; \
       add-apt-repository ppa:jyrki-pulliainen/dh-virtualenv; fi &&\
    env DEBIAN_FRONTEND=noninteractive apt-get install -yqq \
    dpkg-dev \
    debhelper \
    dh-virtualenv \
    git python3 \
    python3-venv \
    python3-dev \
    devscripts \
    equivs

WORKDIR /dpkg-build
COPY ./ ./

# install build-deps
RUN mk-build-deps -i --tool="apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes" debian/control

RUN sed -i -re "1s/..UNRELEASED/~$(echo $BUILDID)$(lsb_release -cs)) $(lsb_release -cs)/" debian/changelog \
    && chmod a-x debian/screamshotter.*
RUN dpkg-buildpackage -us -uc -b
RUN dpkg-buildpackage -S
RUN mkdir -p /dpkg \
    && cp -pl /screamshotter[-_]* /dpkg
RUN dpkg-deb -I /dpkg/screamshotter_*.deb
