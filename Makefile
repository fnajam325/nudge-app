.PHONY: test migrate seed

test:
	python3 -m unittest discover -s tests -t .

migrate:
	python3 -m nudge migrate

seed: migrate
	python3 -m nudge seed
