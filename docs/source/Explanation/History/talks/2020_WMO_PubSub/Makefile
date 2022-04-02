
SCRIPT=script
DIA=Zoning
build: slides script.html

slides: Makefile $(DIA).dia
	awk ' BEGIN { s=0; }; /^Layers/ { s++; printf "dia -t png --size 1920x -e '$(DIA)'_%02d.png -L %s '$(DIA)'.dia \n", s, $$2 ; }; ' $(SCRIPT).txt | sh -x
	touch slides

$(SCRIPT).rst: Makefile $(SCRIPT).txt
	awk ' BEGIN { s=0; }; /^Layers/ { s++; printf "\n.. image:: '$(DIA)'_%02d.png\n   :scale: 75%%\n\n", s; next; }; { print; }; ' $(SCRIPT).txt >$(SCRIPT).rst

$(SCRIPT).html: Makefile $(SCRIPT).rst
	rst2html $(SCRIPT).rst >$(SCRIPT).html


clean: 
	rm $(DIA)_[01]*.png $(SCRIPT).html slides $(SCRIPT).rst

