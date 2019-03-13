src := setup.py oip/ examples/

oip.mpy: oip.py
	python3 -m mpy_cross oip.py

oip.py: $(src)
	cat oip/__init__.py oip/serial.py oip/main.py \
		| grep -v "from \." > oip.py

setup:
	python3 -m pip install -Ur requirements-dev.txt

venv:
	python3 -m venv .venv
	source .venv/bin/activate && make setup
	@echo 'run `source .venv/bin/activate` to use virtualenv'

black:
	isort --apply --recursive $(src)
	black $(src)

lint:
	mypy $(src)
	black --check $(src)
	isort --diff --recursive $(src)

release: lint clean
	python3 setup.py sdist
	python3 -m twine upload dist/*

full:
	python3 oip/generate.py ~/Documents/ObjectsInSpace/serial_commands.txt

tiny:
	python3 oip/generate.py --tiny ~/Documents/ObjectsInSpace/serial_commands.txt

clean:
	rm -rf build dist README MANIFEST oip.egg-info oip.py oip.mpy

distclean: clean
	rm -rf venv .venv
