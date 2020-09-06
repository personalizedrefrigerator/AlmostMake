
VPATH := idontExist folder folder2 folder3/folder4 ../includeTest

include anotherFile.mk

all: a.txt b.txt c.txt d.txt e.txt
	echo $(ANOTHER_FILE) | grep True
	echo "VPATH include test!"

d.txt:
	echo "FAIL" | grep "PASS"

e.txt: anotherFile.mk

.PHONY: all