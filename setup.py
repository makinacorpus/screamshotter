#!/usr/bin/python3

from setuptools import setup, find_packages

with open("src/screamshotter/VERSION", "r") as fh:
    __version__ = fh.read().strip()

setup(
    name='screamshotter',
    version=__version__,
    author='Makina Corpus',
    author_email='support.geotrek@makina-corpus.com',
    url='https://makina-corpus.com',
    description="Takes captures of HTML pages",
    scripts=['src/manage.py'],
    install_requires=[
        'django==4.2.*',
        'backports.zoneinfo==0.2.1;python_version<"3.9"',
        'tzdata',
        'nodeenv',
        'djangorestframework',
        'coreapi',
        'whitenoise',
        # prod
        'gunicorn[gevent]',
        'sentry-sdk',
    ],
    include_package_data=True,
    license='BSD, see LICENSE file.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
)
