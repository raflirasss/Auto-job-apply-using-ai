FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    BROWSER_HEADLESS=true

COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install --with-deps chromium

COPY . .

RUN useradd --create-home --uid 1000 appuser && mkdir -p /app/data /app/config && chown -R appuser /app /ms-playwright
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
