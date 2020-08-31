#!make

check:
	$(MAKE) -C sub2 -j 2
	$(MAKE) -C sub2 -j 3
	$(MAKE) -C sub2 -j -1
	$(MAKE) -C sub2 -j 6
	@echo "-----Testing recursive make with parallelism-----"
	$(MAKE) -C ../testRecursion -j 3

clean: 