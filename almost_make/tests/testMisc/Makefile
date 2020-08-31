#!make

# Test miscellaneous options & features.

clean: 

check: 
	$(MAKE) -C subdir1 -n | grep "echo"
	@echo PASS | grep PASS


.PHONY: check clean