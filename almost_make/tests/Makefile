#!make
# To be run with AlmostMake.
include *.mk

# Perhaps not legal in other versions of make, but it
# should work here. As such, it is tested.
all: testSimple testPhony testMacros testRecursion testParallel testMisc

test%:
	$(MAKE) -C $@ clean $(SEND_MACROS)
	$(MAKE) -C $@ check $(SEND_MACROS)
	$(MAKE) -C $@ clean $(SEND_MACROS)

.PHONY: testSimple testPhony testMacros testRecursion testParallel testMisc
