
VPATH := idontExist folder folder2 folder3/folder4 ../includeTest

include *.mk

all: a.txt *.txt e.txt
	echo $(ANOTHER_FILE) | grep True
	echo $(VIA_DOT) | grep True
	echo "VPATH include test!"

d.txt:
	echo "FAIL" | grep "PASS"

e.txt: anotherFile.mk

.PHONY: all