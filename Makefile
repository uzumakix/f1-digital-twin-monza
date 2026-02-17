.PHONY: run test export clean lint install

install:
	pip install -r requirements-dev.txt

run:
	python main.py

test:
	python -m pytest tests/ -v --tb=short

export:
	python main.py --export both

clean:
	rm -rf .f1_cache/ output/ telemetry_analysis.png
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

lint:
	ruff check src/ tests/ main.py
	ruff format --check src/ tests/ main.py

format:
	ruff format src/ tests/ main.py
