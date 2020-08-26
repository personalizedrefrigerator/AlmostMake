#!make

# Lacking full support for recursive makefiles,
# this script just tests sending flags to child
# make processes.

check: IShouldBreak
    ls | grep IShouldBreak
    exit 123
.PHONY: IShouldBreak
