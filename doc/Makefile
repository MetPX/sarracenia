.SUFFIXES: 

RST2MAN = rst2man
RST2HTML = rst2html
MAKE = make

all: man html

.PHONY: design man html

design: 
	$(MAKE) -C design

html: 
	$(MAKE) -C html
man: 
	$(MAKE) -C man

clean: 
	$(MAKE) -C design clean
	$(MAKE) -C html clean
	$(MAKE) -C man clean


