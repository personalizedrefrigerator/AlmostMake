#!make

# Test miscellaneous options & features.

clean: 

check: bracketCheck
	$(MAKE) -C subdir1 -n | grep "echo"
	$(MAKE) -C includeTest
	@echo PASS | grep PASS

A := F
A := ${A}oo

bracketCheck:
	echo ${A} | grep "Foo"

.PHONY: check clean bracketCheck