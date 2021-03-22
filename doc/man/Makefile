.SUFFIXES: 

RST2MAN = rst2man
RST2HTML = rst2html
MAKE = make

VERSION = $(shell grep __version__ ../../sarracenia/__init__.py | sed -e 's/"//g' | cut -c15-)
DATE = $(shell date "+%B %Y")

MAN1SOURCES = $(wildcard ../*.1.rst)
# MAN1NAMES = $(patsubst ../%.1.rst,%.1,$(MAN1SOURCES))
MAN1TARGETS = $(patsubst ../%.1.rst,%.1,$(MAN1SOURCES))
# MAN1TARGETS = $(MAN1NAMES:.1.rst=.1)

MAN7SOURCES = $(wildcard ../*.7.rst)
MAN7TARGETS = $(patsubst ../%.7.rst,%.7,$(MAN7SOURCES))

MAN8SOURCES = $(wildcard ../*.8.rst)
MAN8TARGETS = $(patsubst ../%.8.rst,%.8,$(MAN8SOURCES))

MANTARGETS = $(MAN1TARGETS) $(MAN7TARGETS) $(MAN8TARGETS)

HTMLSOURCES = $(wildcard *.rst)
HTMLTARGETS = $(HTMLSOURCES:.rst=.html)

all: $(MANTARGETS)

%.1: ../%.1.rst	
	$(RST2MAN) $< $@
	sed -i 's/@Version@/$(VERSION)/' $@
	sed -i 's/@Date@/$(DATE)/' $@

%.7: ../%.7.rst
	$(RST2MAN) $< $@
	sed -i 's/@Version@/$(VERSION)/' $@
	sed -i 's/@Date@/$(DATE)/' $@

%.8: ../%.8.rst
	$(RST2MAN) $< $@
	sed -i 's/@Version@/$(VERSION)/' $@
	sed -i 's/@Date@/$(DATE)/' $@

clean: 
	rm -f $(MANTARGETS) 
