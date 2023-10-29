GOLF_MDB_DIR=~/iNJR/golf/microdb

handicap:
	python handicap.py
	open $(GOLF_MDB_DIR)/index.html
	# miro handicap-counters

upload:
	scp  $(GOLF_MDB_DIR)/*-counters.html $(GOLF_MDB_DIR)/*-handicap.html microdb:/microdb/static/golf


combined:
	# save to excel
	python3 extract.py
	miro -f analyse
	python3 adjust.py
	pdflatex combinedhandicaps

medals:
	# save to excel
	python3 extract.py
	# Copy any medals to medals.txt, replacing stake with CSS
	# and adding in exact handicap
	miro -f analyse medals
	python3 adjust.py medals
	pdflatex medalhandicaps

