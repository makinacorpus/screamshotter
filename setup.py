#!/usr/bin/python3
from setuptools import setup, find_packages

setup(
    name='screamshotter2',
    version='0.0.9+dev',
    author='Makina Corpus',
    author_email='support.geotrek@makina-corpus.com',
    url='http://makina-corpus.com',
    description="Takes captures of HTML pages",
    install_requires=[
        'django',
        'nodeenv',
        'djangorestframework',
        'coreapi',
        # dev & tests
        'coverage',
        'flake8',
        'Pillow',
        'python-magic',
        # dev project
        'django-debug-toolbar',
        # prod
        'gunicorn[gevent]',
        'whitenoise'
    ],
    include_package_data=True,
    license='BSD, see LICENSE file.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
)
