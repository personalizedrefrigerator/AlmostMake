
check: 
	touch d.dep.txt
	touch d.txt
	sleep 0.1
	touch a.dep.txt
	touch b.dep.txt
	touch c.dep.txt
	$(MAKE) a.txt b.txt c.txt
	sleep 0.1

#    Should cause b and, by extension, a, to rebuild:
#	  As such, only the commands touch b.txt and touch a.txt
#	  should be run.
	touch b.dep.txt
	$(MAKE) a.txt | grep -v "touch b.txt" | grep -cx "touch a.txt" | grep 1


a.txt: a.dep.txt b.txt
	touch a.txt

b.txt: b.dep.txt d.txt
	touch b.txt

c.txt: c.dep.txt
	touch c.txt

d.txt:
	echo "FAIL, should not have attempted to make d.txt." | grep "PASS"



clean:
	-rm *.txt

.PHONY: check clean
