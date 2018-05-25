install: bin/python

bin/python:
	virtualenv .
	bin/python setup.py develop

serve: bin/python
	bin/python ./manage.py runserver 8888

gunicorn: bin/python
	bin/pip install gunicorn

deploy: bin/python
	touch screamshotter/wsgi.py  # trigger reload

clean:
	rm -rf bin/ lib/ build/ dist/ *.egg-info/ include/ local/