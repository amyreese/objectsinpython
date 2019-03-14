src := setup.py oip/ examples/

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

full: $(src)
	python3 oip/generate.py ~/Documents/ObjectsInSpace/serial_commands.txt
	cat oip/__init__.py oip/serial.py oip/main.py \
		| grep -v "from \." > oip.py
	python3 -m mpy_cross oip.py

tiny: $(src)
	python3 oip/generate.py ~/Documents/ObjectsInSpace/serial_commands.txt
	cat oip/__init__.py oip/serial.py oip/main.py \
		| grep -v "from \." > oip-tiny.py
	python3 -m mpy_cross oip-tiny.py

clean:
	rm -rf build dist README MANIFEST oip.egg-info oip*.py oip*.mpy

distclean: clean
	rm -rf venv .venv
