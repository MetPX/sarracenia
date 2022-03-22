
BUILDDIR=../../../../build/html/Explanation/History/talks/10minutes

build: slides script.html

slides: Makefile ../A2B.dia
	mkdir -p ../$(BUILDDIR)
	awk ' BEGIN { s=0; }; /^Layers/ { s++; printf "dia -t png --size 1920x -e '$(BUILDDIR)'/a2b_%02d.png -L %s A2B.dia \n", s, $$2 ; }; ' ../script.txt | (cd ..; sh -x)

script.rst: Makefile ../script.txt
	awk ' BEGIN { s=0; }; /^Layers/ { s++; printf "\n.. image:: a2b_%02d.png\n   :scale: 25%\n\n", s; next; }; { print; }; ' ../script.txt >script.rst

script.html: Makefile script.rst
	rst2html script.rst >../$(BUILDDIR)/index.html


clean: 
	rm a2b_*.png script.html slides script.rst

