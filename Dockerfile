FROM python:3.12-slim


WORKDIR /app


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY scripts ./scripts
COPY tests ./tests
COPY pytest.ini .

RUN chmod +x ./scripts/start.sh


RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser \
    && chown -R appuser:appuser /app


USER appuser


CMD ["./scripts/start.sh"]
