ARG DISTRO=ubuntu:jammy

FROM ${DISTRO} AS base

RUN apt-get update -qq -o Acquire::Languages=none && \
    env DEBIAN_FRONTEND=noninteractive apt-get update -qq -o Acquire::Languages=none && apt-get install -yqq \
    dpkg-dev \
    debhelper \
    dh-virtualenv \
    git \
    devscripts \
    equivs

WORKDIR /dpkg-build
COPY ../debian ./debian

RUN env DEBIAN_FRONTEND=noninteractive mk-build-deps --install --tool='apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes' debian/control

COPY .. ./
WORKDIR /dpkg-build

RUN sed -i -re "1s/..UNRELEASED/.ubuntu$(lsb_release -rs)) $(lsb_release -cs)/" debian/changelog \
    && chmod a-x debian/screamshotter.* \
    && dpkg-buildpackage -us -uc -b && mkdir -p /dpkg && cp -pl /screamshotter[-_]* /dpkg \
    && dpkg-deb -I /dpkg/screamshotter*.deb
WORKDIR /dpkg
