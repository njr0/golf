PYTHON=python3.11
GOLF_MDB_DIR=/Users/njr/iNJR/golf/microdb

.PHONY: all tracker upload

tracker:
	$(PYTHON) tracker.py -n
	sudo cp ~/tracker/* /microdb/static/golf
	sudo chown apache /microdb/static/golf/*

upload:
	scp -i /Users/njr/.ssh/microdb_cline_id_rsa $(GOLF_MDB_DIR)/index.html \
            $(GOLF_MDB_DIR)/Tracker*.html \
            $(GOLF_MDB_DIR)/Round*.html \
            microdb:/microdb/static/golf
