PYTHON ?= python

.PHONY: venv install profile data power charts notebook views all clean

venv:
	$(PYTHON) -m venv .venv

install:
	$(PYTHON) -m pip install -r requirements.txt

profile:
	$(PYTHON) src/profile_data.py

data:
	$(PYTHON) src/run_queries.py

power:
	$(PYTHON) src/power_analysis.py

charts:
	$(PYTHON) src/charts.py

views:
	$(PYTHON) src/create_views.py

notebook:
	jupyter nbconvert --to notebook --execute --inplace analysis.ipynb

all: profile data power charts views notebook

clean:
	rm -f data/*.csv charts/*.png
