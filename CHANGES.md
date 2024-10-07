CHANGELOG
=========

2.2.4        (2024-10-07)
-------------------------

* Fix dependencies with python 3.10


2.2.3        (2024-10-04)
-------------------------

* Dependencies update


2.2.2        (2024-01-19)
-------------------------

**Bugfix**:

* Fix chromium crash after debian update from previous version


2.2.1        (2024-01-11)
-------------------------

**Improvements**:

* Ignore SSL errors with external browser


2.2.0        (2024-01-11)
-------------------------

**New features**

* Allow to use external browser with `EXTERNAL_PUPPETEER` environment variable


2.1.0        (2023-11-24)
-------------------------

**Improvements**:

* Update to node 20, puppeteer and chromium


2.0.21       (2023-11-22)
-------------------------

**Bugfix**:

* Fix chromium zombie processes in docker image


2.0.20       (2023-11-06)
-------------------------

**New features**

* Add `screamshotter_css_class` to allow to change css class to inject in body.


2.0.19       (2022-10-04)
-------------------------

* Add MAX_REQUESTS environment restart gunicorn workers to prevent memory leaks. Default to 250.
* Force kill chromium process after screenshots.


2.0.18       (2022-07-13)
-------------------------

* Add sentry documentation

**Bugfix**:

* TIMEOUT settings from environment is now cast in integer


2.0.17       (2022-06-16)
-------------------------

* Fix debian package dependencies.


2.0.16       (2022-05-11)
-------------------------

* Fix debian packaging deployment


2.0.15       (2022-05-03)
-------------------------

* Add sentry in package and docker


2.0.14       (2022-01-21)
-------------------------

* New release to fix debian packaging


2.0.13       (2022-01-21)
-------------------------

* Fix zombie processes
* Update python libraries


2.0.12   (2021-11-30)
---------------------

* Add environment's variable : timeout for gunicorn and puppeteer


2.0.11   (2021-06-02)
---------------------

* Bugfix static files in docker image


2.0.10   (2021-04-27)
---------------------

* Bugfix static files in docker image


2.0.9    (2021-04-21)
---------------------

* Bugfix official publication


2.0.8    (2021-04-21)
---------------------

* Bugfix official publication


2.0.7    (2021-04-21)
---------------------

* Official publication


2.0.6    (2021-04-21)
---------------------

* Increase Puppeteer default timeouts
* Optimize npm install in debian packages


2.0.5    (2021-04-20)
---------------------

* Fix secret key management
* Fix NODE_BIN_PATH in debian package


2.0.4    (2021-04-20)
---------------------

* Improve and fix package building


2.0.3    (2021-04-19)
---------------------

* Fix ALLOWED_HOSTS to accept all by default and permit customization in environment.


2.0.2    (2021-04-19)
---------------------

* Fix ALLOWED_HOSTS to accept all by default and permit customization in environment.

2.0.1    (2021-04-19)
---------------------

* Fix a backward compatibility with v1 by renaming project folder


2.0.0    (2021-04-16)
---------------------

* Initial v2 release
* From CasperJS / PhantomJS to Puppeteer / Chromium
