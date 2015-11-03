.SUFFIXES: .1.rst .5 .7 .dia .png .pdf .html


#Guide.rtf:   Guide.latex
#	latex2rtf </dev/null Guide.latex >Guide.rtf

MANPAGES= dd_sara.1.html dd_subscribe.1.html dd_watch.1.html dd_post.1.html dd_post.7.html dd_log.7.html dd_log2clusters.8.html dd_log2source.8.html

TARGETS= $(MANPAGES)

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
dd_sara.1.html: ../dd_sara.1.rst
	rst2html ../dd_sara.1.rst >dd_sara.1.html

dd_subscribe.1.html: ../dd_subscribe.1.rst
	rst2html ../dd_subscribe.1.rst >dd_subscribe.1.html

dd_watch.1.html: ../dd_watch.1.rst
	rst2html ../dd_watch.1.rst >dd_watch.1.html

dd_post.1.html: ../dd_post.1.rst
	rst2html ../dd_post.1.rst >dd_post.1.html

dd_post.7.html: ../dd_post.7.rst
	rst2html ../dd_post.7.rst >dd_post.7.html

dd_log2clusters.8.html: ../dd_log2clusters.8.rst
	rst2html ../dd_log2clusters.8.rst >dd_log2clusters.8.html

dd_log2source.8.html: ../dd_log2source.8.rst
	rst2html ../dd_log2source.8.rst >dd_log2source.8.html

dd_log.7.html: ../dd_log.7.rst
	rst2html ../dd_log.7.rst >dd_log.7.html

clean: 
	rm -f $(TARGETS) *.png 



