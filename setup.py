#!/usr/bin/python3
from src.screamshotter import __version__
from setuptools import setup, find_packages

setup(
    name='screamshotter',
    version=__version__,
    author='Makina Corpus',
    author_email='support.geotrek@makina-corpus.com',
    url='https://makina-corpus.com',
    description="Takes captures of HTML pages",
    scripts=['src/manage.py'],
    install_requires=[
        'django',
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
