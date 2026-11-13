PYTHON ?= python

.PHONY: venv data charts notebook views all clean

venv:
	$(PYTHON) -m venv .venv

install:
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) src/run_queries.py

charts:
	$(PYTHON) src/charts.py

views:
	$(PYTHON) src/create_views.py

notebook:
	jupyter nbconvert --to notebook --execute --inplace analysis.ipynb

all: data charts views notebook

clean:
	rm -f data/*.csv charts/*.png
