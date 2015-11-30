.SUFFIXES: .1.rst .5 .7 .dia .png .pdf .html


#Guide.rtf:   Guide.latex
#	latex2rtf </dev/null Guide.latex >Guide.rtf

GUIDES= Dev.html Admin.html indexe.html indexf.html

MANPAGES= sr_sarra.8.html sr_subscribe.1.html dd_subscribe.1.html sr_watch.1.html sr_post.1.html sr_post.7.html sr_log.7.html sr_log2clusters.8.html log2clusters.7.html sr_log2source.8.html

TARGETS= $(MANPAGES) $(GUIDES)

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

sr_sarra.8.html: ../sr_sarra.8.rst
	rst2html ../sr_sarra.8.rst >sr_sarra.8.html

sr_subscribe.1.html: ../sr_subscribe.1.rst
	rst2html ../sr_subscribe.1.rst >sr_subscribe.1.html

dd_subscribe.1.html: ../dd_subscribe.1.rst
	rst2html ../dd_subscribe.1.rst >dd_subscribe.1.html

sr_watch.1.html: ../sr_watch.1.rst
	rst2html ../sr_watch.1.rst >sr_watch.1.html

sr_post.1.html: ../sr_post.1.rst
	rst2html ../sr_post.1.rst >sr_post.1.html

sr_post.7.html: ../sr_post.7.rst
	rst2html ../sr_post.7.rst >sr_post.7.html

log2clusters.7.html: ../log2clusters.7.rst
	rst2html ../log2clusters.7.rst >log2clusters.7.html

sr_log2clusters.8.html: ../sr_log2clusters.8.rst
	rst2html ../sr_log2clusters.8.rst >sr_log2clusters.8.html

sr_log2source.8.html: ../sr_log2source.8.rst
	rst2html ../sr_log2source.8.rst >sr_log2source.8.html

sr_log.7.html: ../sr_log.7.rst
	rst2html ../sr_log.7.rst >sr_log.7.html

AMQP4Sarra.svg: ../AMQP4Sarra.dia
	dia -t svg  -e $@ ../AMQP4Sarra.dia


Dev.html: ../Dev.rst
	rst2html ../Dev.rst >Dev.html

Admin.html: ../Admin.rst AMQP4Sarra.svg
	rst2html ../Admin.rst >Admin.html

indexe.html: ../indexe.rst
	rst2html ../indexe.rst >indexe.html

indexf.html: ../indexf.rst
	rst2html ../indexf.rst >indexf.html

clean: 
	rm -f $(TARGETS) 



