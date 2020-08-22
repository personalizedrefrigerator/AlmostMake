#!make

check: macroTest
clean:

.PHONY: check clean macroTest


macroTest:
	echo $(PATH) | grep $(shell echo $PATH)
	echo "$(TEST_MACRO)" | grep "Testing1234=:= := This 'should ' work!"
	$(MAKE) -C overrideMacrosTest DOES_IT_OVERRIDE=YesItDoes
