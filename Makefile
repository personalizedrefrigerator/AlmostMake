#!make

all: 
	@echo "Help:"
	@echo -n "    \033[32mplay:\033[0m"
	@echo " This one is important! It installs the current version of almost_make to permit testing. Don't use this unless you want to install a version of almake!"
	@echo "    test: Depends on play. Runs tests using almost_make installation."
	@echo "    shell: Depends on play. Open an interface to the built-in shell."
	@echo "    clean, full-clean: Clean up after play, build."
	@echo "    build: Generate distribution archives. See https://packaging.python.org/tutorials/packaging-projects/"
	@echo "    publish: Push to testpypi. If the version-numbers in setup.py are out-of-date, this may fail."

# Install! We can test the command through 'almake'!
# Danger! This installs almake! Do not run this if you don't want to install
# it!
play: clean build
	python3 -m pip install --force-reinstall .
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
	cd almost_make/tests; python3 ../cli.py
	cd almost_make/utils/shellUtil; python3 runner.py

testEnv:
	python3 -m venv $@

full-clean: clean
	-rm -rf testEnv
	-rm -rf almost_make.egg-info

.PHONY: full-clean clean publish build play shell
