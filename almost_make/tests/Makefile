# To be run with AlmostMake.
include *.mk

all: testSimple testPhony testMacros testRecursion testParallel testMisc testModTime \
		testCannedRecipes

# Perhaps not legal in other versions of make, but it
# should work here. As such, it is tested.
test%:
	$(MAKE) --undefined-is-error -C $@ clean
	$(MAKE) --undefined-is-error -C $@ check
	$(MAKE) --undefined-is-error -C $@ clean

.PHONY: testSimple testPhony testMacros testRecursion testParallel testMisc testModTime \
		testCannedRecipes
