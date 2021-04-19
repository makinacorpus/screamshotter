#!/usr/bin/python3
from setuptools import setup, find_packages

setup(
    name='screamshotter',
    version='2.0.4+dev',
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
