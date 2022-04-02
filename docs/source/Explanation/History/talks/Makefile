.SUFFIXES: .1 .rst .5 .7 .dia .svg .png .jpeg .pdf .html


#Guide.rtf:   Guide.latex
#	latex2rtf </dev/null Guide.latex >Guide.rtf


BUILDDIR= ../../../build/html
IMAGES= AMQP4Sarra.svg
SLIDESHOWS= AMQPprimer.html

TARGETS= $(IMAGES) $(SLIDESHOWS)

default: $(TARGETS) 

.dia.svg:
	dia -t svg $*.dia

.dia.png:
	dia -t png $*.dia

.rst.html:
	rst2html $*.rst >$@



# a2b_*.png are just leftovers:
a2b_1.png: A2B.dia
	dia -t png --size 1024x -e $@ -L Background A2B.dia

clean: 
	rm -f $(TARGETS) 



