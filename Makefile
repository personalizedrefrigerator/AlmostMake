#!make

# Install! We can test the command through 'almake'!
play: clean build
	python3 -m pip install --force-reinstall -e .
	#bash -c "cd testEnv; source bin/activate; python3 -m pip install ../"

# Test the embedded shell!
shell: play
	python3 almost_make/utils/shellUtil/shellUtil.py

# Prepare AlmostMake for submission to PyPi!
# See https://packaging.python.org/tutorials/packaging-projects/
build:
	python3 setup.py sdist bdist_wheel

publish: build
	python3 -m twine upload --repository testpypi dist/*

clean:
	-rm -rf dist
	-rm -rf almost_make_personalizedrefrigerator.egg-info
	-rm -rf build

test: play
	cd almost_make/tests; almake
	cd almost_make/utils/shellUtil; python3 runner.py

testEnv:
	python3 -m venv $@

full-clean: clean
	-rm -rf testEnv
	-rm -rf almost_make.egg-info

.PHONY: full-clean clean publish build play shell
