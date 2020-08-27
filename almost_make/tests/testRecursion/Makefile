#!make

# Lacking full support for recursive makefiles,
# this script just tests sending flags to child
# make processes.

check: doesNotPersist goesToChild

clean:

.PHONY: check clean goesToChild doesNotPersist


doesNotPersist:
	$(MAKE) --help | grep "Help:"
	cd subdir1 && $(MAKE) subdir1 | grep "I am not printing help."

goesToChild:
	$(MAKE) -C goesToChild -ks
