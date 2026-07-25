.PHONY: run_ut
run_ut:
	python -m unittest discover -s . -p 'test_*.py'

build:
	pyinstaller -F taskrunner.py
