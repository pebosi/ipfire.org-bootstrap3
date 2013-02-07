
PO_PATH = translations
POTFILE = $(PO_PATH)/webapp.pot
POFILES = $(wildcard $(PO_PATH)/*/LC_MESSAGES/*.po)

ALL_FILES = $(shell find . /usr/lib*/python*/site-packages/tornado -name "*.py" -or -name "*.html")

.PHONY: pot
pot: $(POTFILE)

$(POTFILE): $(ALL_FILES)
	xgettext --language=Python --from-code=UTF-8 --keyword=_:1,2 --keyword=N_ -d pakfire -o $(POTFILE) \
		$(ALL_FILES)

.PHONY: po
po: $(POTFILE) $(patsubst %.po, %.mo, $(POFILES))

%.po: $(POTFILE)
	# Merge the POTFILE.
	msgmerge $@ $(POTFILE) -o $@

%.mo: %.po
	# Compile the translations.
	msgfmt $< -o $@
