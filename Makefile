# Path to your Green Metrics Tool installation
GMT_DIR := /Users/brandao/green-metrics-tool
VENV := ./venv/bin/activate

run:
	cd $(GMT_DIR) && \
	source $(VENV) && \
	python3 runner.py --uri /Users/brandao/mthesis --name run
