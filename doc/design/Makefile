
.SUFFIXES: .rst .5 .7 .dia .png .pdf .html


#Guide.rtf:   Guide.latex
#	latex2rtf </dev/null Guide.latex >Guide.rtf

TARGETS= accounts.html biblio.html components.html configuration.html sr_post_sample.html deltas.html design.html message_considerations.html messages_v02.html monitoring.html Outline.html packaging.html plan.html scope.html use-cases/use_cases.html validation.html webification.html private.html index.html

default: $(TARGETS) 

.rst.html:
	rst2html $*.rst >$*.html

clean:
	rm -f $(TARGETS)
