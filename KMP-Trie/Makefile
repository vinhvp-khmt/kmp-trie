.PHONY: test benchmark figures report slides verify artifacts

test:
	python -m pytest tests/ -q
	python -m pytest --doctest-modules src/ tests/baseline.py -q
	python -m demo.web --self-test

benchmark:
	python scripts/run_benchmark.py --repeat 7

figures:
	python scripts/plot_results.py

report:
	bash report/latex/build/make.sh

slides:
	bash slides/build/make.sh

verify:
	python scripts/verify_artifacts.py

artifacts: report slides
	python scripts/verify_artifacts.py
