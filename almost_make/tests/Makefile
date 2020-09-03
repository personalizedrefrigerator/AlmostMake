#!make
# To be run with AlmostMake.
include *.mk

# Perhaps not legal in other versions of make, but it
# should work here. As such, it is tested.
all: testSimple testPhony testMacros testRecursion testParallel testMisc

test%:
	$(MAKE) -C $@ clean
	$(MAKE) -C $@ check
	$(MAKE) -C $@ clean

.PHONY: testSimple testPhony testMacros testRecursion testParallel testMisc
