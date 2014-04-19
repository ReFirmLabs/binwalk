check_PROGRAMS = test
test_LDADD = $(top_builddir)/src/libmagic.la
test_CPPFLAGS = -I$(top_srcdir)/src

EXTRA_DIST = \
escapevel.result \
escapevel.testfile \
gedcom.result \
gedcom.testfile \
issue311docx.result \
issue311docx.testfile

T = $(top_srcdir)/tests
check-local:
	MAGIC=$(top_builddir)/magic/magic ./test
	for i in $T/*.testfile; do echo Running test: $$i; MAGIC=$(top_builddir)/magic/magic ./test $$i $${i%%.testfile}.result; done
