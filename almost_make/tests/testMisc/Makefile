#!make

# Test miscellaneous options & features.

clean: 

check: bracketCheck vpathCheck vpathCheck2 test2
	$(MAKE) -C subdir1 -n | grep "echo"
	$(MAKE) -C includeTest
	@echo PASS | grep PASS

A := F
A := ${A}oo

${A}2:
	echo ${A} | grep "Foo"

bracketCheck: Foo2
	echo ${A} | grep "Foo"

vpathCheck%:
	cd $@ && $(MAKE)

# A GNUMake-style empty recipe
test2:	;

.PHONY: check clean bracketCheck $(A)2 vpathCheck vpathCheck2