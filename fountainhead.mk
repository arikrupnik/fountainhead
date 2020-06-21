# fountainhead.mk: include this file from you Makefile to process
# Fountain.io screenplays

# Paths to DTDs and stylesheets are relative to this file; to help
# make(1) find them, include this file like so from your own makefile:
#
# FOUNTAINHEADDIR=path/to/fountainhead
# include $(FOUNTAINHEADDIR)/fountainhead.mk


# DEPENDENCIES

PYTHON=python
# https://pypi.python.org/pypi/Markdown
# http://xmlsoft.org/XSLT/xsltproc2.html
XSLTPROC=xsltproc
# http://xmlsoft.org/xmllint.html
XMLLINT=xmllint
# http://pandoc.org/
PANDOC=pandoc
# http://weasyprint.org/
WEASYPRINT=python3 -m weasyprint
ASPELL=aspell
GREP=grep
GIT=git

# SPELLCHECK: verifies .fountain and .md files. Projects can add local
# dictionary terms in $(DICT_FILE). aspell(1) requires that the
# filename be absolute or start with `./' (the value below would need
# refinement in case of recursive make(1) invocations)
DICT_FILE=./aspell.en.pws

.SUFFIXES: .fountain .d .ftx .pdf .md .html .plot-summary

GIT_VERSION=$(shell $(GIT) describe --tags || $(GIT) rev-parse --short HEAD)

# FOUNTAIN toolchain: .fountain.ftx.pdf

# XML from fountain
%.ftx : %.fountain %.d
	$(PYTHON) $(FOUNTAINHEADDIR)/fountainhead.py -M $< > $*.d
	$(PYTHON) $(FOUNTAINHEADDIR)/fountainhead.py -sx -m Version "$(GIT_VERSION)" -c $(FOUNTAINHEADDIR)/ftx.css $< > $@_
	$(XMLLINT) --noout --dtdvalid $(FOUNTAINHEADDIR)/ftx.dtd $@_
	$(ASPELL) list -H -p $(DICT_FILE) < $@_ > $@_nondict
	if [ -s $@_nondict ]; then $(GREP) -nwFf $@_nondict --color=auto $< `sed 's/^.*://' $*.d`; rm $@_nondict; exit 1; fi
	rm $@_nondict
	mv $@_ $@
# http://make.mad-scientist.net/papers/advanced-auto-dependency-generation/
# doesn't quite work: mising .d fails to force rebuild
%.d : ;
.PRECIOUS: %.d
include $(wildcard *.d)

# FTX+CSS can render directly in browsers and to PDF, without HTML
# intermediary
.ftx.pdf:
	$(WEASYPRINT) -s $(FOUNTAINHEADDIR)/ftx.css $< $@
%-bd.pdf : %.ftx
	$(WEASYPRINT) -s $(FOUNTAINHEADDIR)/ftx.css -s $(FOUNTAINHEADDIR)/ftx-bd.css $< $@


# markdown toolchain: .md.html.pdf

# markdown renders through HTML intermediary (with TW-style CSS)
.md.html:
	$(ASPELL) list -p $(DICT_FILE) < $< | $(GREP) -nwFf - --color=auto $<; \
		[ $$? -eq 1 ]
	$(PANDOC) -H $(FOUNTAINHEADDIR)/typewriter_css.inc -o $@ $<

# weasyprint PDF from HTML
.html.pdf:
	$(WEASYPRINT) $< $@

# additional artifacts from .fountain

# markdown plot summary
.ftx.plot-summary:
	$(XSLTPROC) -o $@ $(FOUNTAINHEADDIR)/plot-summary.xslt $<
