.PHONY: help run-dry run run-save test lint

help:
	@echo "targets:"
	@echo "  run-dry   offline mock model; prints proposal; no file writes, no git"
	@echo "  run       real model (needs ANTHROPIC_API_KEY); prints proposal; no commits"
	@echo "  run-save  real model; also saves proposal-<date>.md into ./proposals/ for review"
	@echo "  test      run the full unittest suite"

run-dry:
	python3 -m agent.run --mock

run:
	python3 -m agent.run

run-save:
	python3 -m agent.run --save proposals/

test:
	python3 -m unittest discover tests -v
