run:
	honcho start -f Procfile.dev
test_server:
	pipenv run python test.py
