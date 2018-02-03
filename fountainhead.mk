# fountainhead.mk: include this file from you Makefile to process
# Fountain.io screenplays

# Paths to DTDs and stylesheets are relative to this file; to help
# make(1) find them, include this file like so from your own makefile:
#
# FOUNTAINHEADDIR=path/to/fountainhead
# include $(FOUNTAINHEADDIR)/fountainhead.mk


# DEPENDENCIES

# https://github.com/olivertaylor/Textplay (fountainhead includes this
# as a submodule)
TEXTPLAY=$(FOUNTAINHEADDIR)/Textplay/textplay
# http://xmlsoft.org/XSLT/xsltproc2.html
XSLTPROC=xsltproc
# http://xmlsoft.org/xmllint.html
XMLLINT=xmllint
# http://pandoc.org/
PANDOC=pandoc
# http://weasyprint.org/
WEASYPRINT=weasyprint

.SUFFIXES: .fountain .tpx .ftx .pdf .md .html

# FOUNTAIN toolchain: .fountain.tpx.ftx.pdf

# textplay XML from fountain
.fountain.tpx:
	$(TEXTPLAY) -x < $< > $@

# fountainhead XML (with structure, etc.)
.tpx.ftx:
	$(XSLTPROC) -o $@ $(FOUNTAINHEADDIR)/tpx2ftx.xslt $<
	$(XMLLINT) --noout --dtdvalid $(FOUNTAINHEADDIR)/ftx.dtd $@

# FTX+CSS can render directly in browsers and to PDF, without HTML
# intermediary
.ftx.pdf:
	$(WEASYPRINT) -s $(FOUNTAINHEADDIR)/ftx.css $< $@


# markdown toolchain: .md.html.pdf

# markdown renders through HTML intermediary (with TW-style CSS)
.md.html:
	$(PANDOC) -H $(FOUNTAINHEADDIR)/typewriter_css.inc -o $@ $<

# weasyprint PDF from HTML
.html.pdf:
	$(WEASYPRINT) $< $@
