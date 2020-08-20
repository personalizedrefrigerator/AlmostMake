#!make

# Checks whether the presence of .PHONY files 
# prevents the execution of rules.

check: createMain
	ls | grep "main.txt"
	ls | grep "main2.txt"

clean:
	-rm -rf main.txt
	-rm -rf main2.txt

createMain: makeMain
	ls | grep "main.txt"
	touch main2.txt

makeMain:
	touch main.txt

.PHONY: makeMain createMain check clean
