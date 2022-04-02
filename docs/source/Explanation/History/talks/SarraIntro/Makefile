
BUILDDIR=../../../../../build/html/Explanation/History/talks/SarraIntro

build: $(BUILDDIR)/a2b_01.png $(BUILDDIR)/index.html

$(BUILDDIR)/a2b_01.png: Makefile A2B.dia 
	mkdir -p ../$(BUILDDIR)
	awk ' BEGIN { s=0; }; /^Layers/ { s++; printf "dia -t png --size 1920x -e '$(BUILDDIR)'/a2b_%02d.png -L %s A2B.dia \n", s, $$2 ; }; ' script.txt | sh -x

$(BUILDDIR)/index.html: index.rst script.txt
	awk ' BEGIN { s=0; }; /^Layers/ { s++; printf "\n.. image:: a2b_%02d.png\n   :scale: 25%\n\n", s; next; }; { print; }; ' script.txt >index.rst

clean: 
	rm a2b_*.png script.html slides index.rst

