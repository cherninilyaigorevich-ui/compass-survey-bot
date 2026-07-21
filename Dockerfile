FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY scripts ./scripts


RUN chmod +x ./scripts/start.sh


CMD ["./scripts/start.sh"]
