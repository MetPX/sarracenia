.SUFFIXES: .1 .5 .7 .dia .png .pdf .html


#Guide.rtf:   Guide.latex
#	latex2rtf </dev/null Guide.latex >Guide.rtf

MANPAGES= dd_subscribe.1.html dd_watch.1.html dd_post.1.html dd_post.7.html dd_log.7.html

TARGETS= $(MANPAGES)

default: $(TARGETS) 

.dia.png:
	dia -t png $*.dia


# there should be a way to make an implicit rule for the man pages,
# some sort of thing that would scan all of man tree, and do the right
# thing...
# but copy paste was faster...
# when you add a man page, need to:
#         -- add an explicit target here.
#         -- add a link from index.html.
#
dd_subscribe.1.html: ../../man/man1/dd_subscribe.1
	groff -Thtml -man ../../man/man1/dd_subscribe.1 >dd_subscribe.1.html

dd_watch.1.html: ../../man/man1/dd_watch.1
	groff -Thtml -man ../../man/man1/dd_watch.1 >dd_watch.1.html

dd_post.1.html: ../../man/man1/dd_post.1
	groff -Thtml -man ../../man/man1/dd_post.1 >dd_post.1.html

dd_post.7.html: ../../man/man7/dd_post.7
	groff -Thtml -man ../../man/man7/dd_post.7 >dd_post.7.html

dd_log.7.html: ../../man/man7/dd_log.7
	groff -Thtml -man ../../man/man7/dd_log.7 >dd_log.7.html

clean: 
	rm -f $(TARGETS) *.png 



