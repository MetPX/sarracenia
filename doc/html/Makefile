.SUFFIXES: .1.rst .5 .7 .dia .png .pdf .html


#Guide.rtf:   Guide.latex
#	latex2rtf </dev/null Guide.latex >Guide.rtf

VERSION = $(shell grep __version__ ../../sarra/__init__.py | sed -e 's/"//g' | cut -c14-)
DATE = $(shell date "+%B %Y")

SOURCES = $(wildcard ../*.rst)
TARGETS = $(patsubst ../%.rst,%.html,$(SOURCES))

default: $(TARGETS) 

.dia.png:
	dia -t png $*.dia

.rst.html:
	rst2html $*.rst >$*.html

# there should be a way to make an implicit rule for the man pages,
# some sort of thing that would scan all of man tree, and do the right
# thing...
# but copy paste was faster...
# when you add a man page, need to:
#         -- add an explicit target here.
#         -- add a link from index.html.
#

%.html: ../%.rst	
	rst2html $< $@	
	sed -i 's/&\#64;Date&\#64;/$(DATE)/' $@
	sed -i 's/&\#64;Version&\#64;/$(VERSION)/' $@


clean: 
	rm -f $(TARGETS) 
