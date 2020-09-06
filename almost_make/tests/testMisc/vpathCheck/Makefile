
VPATH := folder:folder2:folder3/folder4:../includeTest

all: a.txt b.txt c.txt d.txt e.txt

d.txt:
	echo "FAIL" | grep "PASS"

e.txt: anotherFile.mk