.PHONY: test up down logs build backup


up:
	docker compose up -d


down:
	docker compose down


build:
	docker compose build


logs:
	docker compose logs -f app


test:
	docker compose \
		-f compose.test.yaml \
		run --rm app-test pytest
