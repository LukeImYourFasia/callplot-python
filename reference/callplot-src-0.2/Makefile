README_FILES=LICENSE.txt README_CALLPLOT.txt # README_PLOTTABLE.txt 
SCRIPTS=callplot.sh # plottable.sh
JARS=lib/callplot.jar
LIBFILES=# $(wildcard lib/*.xsl)
SOURCES=$(shell find com -name *.java -print)
BUILD_FILES=manifest Makefile version.txt

VERSION=callplot-$(shell cat version.txt)
SRCVERSION=callplot-src-$(shell cat version.txt)

all: build # test package 

build: $(JARS)

$(JARS) : $(SOURCES)
	javac $(SOURCES)
	jar cvmf manifest callplot.jar com/*/*/*.class
	mkdir -p lib
	cp callplot.jar lib/

TEST_SOURCES=samples/fred samples/fred2 samples/fred_annot

ASCII_TARGETS=$(patsubst %,%.aa,$(TEST_SOURCES))
VML_TARGETS=$(patsubst %,%.vml,$(TEST_SOURCES))
XML_TARGETS=$(patsubst %,%.xml,$(TEST_SOURCES))
PIC_TARGETS=$(patsubst %,%.pic,$(TEST_SOURCES))
PDF_TARGETS=$(patsubst %,%.pdf,$(TEST_SOURCES))
SVG_TARGETS=$(patsubst %,%.svg,$(TEST_SOURCES))

TEST_TARGETS=$(ASCII_TARGETS) $(VML_TARGETS) $(XML_TARGETS) $(SVG_TARGETS) $(PIC_TARGETS)

%.aa : %
	./callplot.sh $< >$@

%.vml : %
	./callplot.sh -vml $< >$@

%.xml : %
	./callplot.sh -xml $< >$@

%.pic : %
	./callplot.sh -pic $< >$@

%.svg : %
	./callplot.sh -svg $< >$@

%.pdf : %.pic
	pic $< | groff -Tps | ps2pdf - $@

$(TARGET_DIR):
	mkdir $(TARGET_DIR)

test: $(TEST_TARGETS)

pdftest: $(PDF_TARGETS)

clean:
	rm $(TEST_TARGETS) $(PDF_TARGETS) $(JARS)

package: $(JARS)
	tar cvf $(VERSION).tar $(SCRIPTS) $(README_FILES) $(JARS) $(LIBFILES) $(TEST_SOURCES)
	rm -rf $(VERSION)
	mkdir $(VERSION)
	( cd $(VERSION) ; tar xvf ../$(VERSION).tar )
	rm $(VERSION).tar
	tar cvzf $(VERSION).tgz $(VERSION)
	rm -rf $(VERSION)

srcpackage:
	tar cvf $(SRCVERSION).tar $(SCRIPTS) $(README_FILES) $(SOURCES) $(BUILD_FILES) $(LIBFILES) $(TEST_SOURCES)
	rm -rf $(SRCVERSION)
	mkdir $(SRCVERSION)
	( cd $(SRCVERSION) ; tar xvf ../$(SRCVERSION).tar )
	rm $(SRCVERSION).tar
	tar cvzf $(SRCVERSION).tgz $(SRCVERSION)
	rm -rf $(SRCVERSION)
