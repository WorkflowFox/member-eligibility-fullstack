# Container image for the api service. Per issue #8: package the FastAPI
# app together with a seeded SQLite database baked in at build time.

FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only. requirements-dev.txt (pytest, httpx,
# etc.) is intentionally never copied or installed here.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code. tests/, requirements-dev.txt, pytest.ini, and other dev-only
# files are excluded from the build context via .dockerignore.
COPY . .

# Bake the seeded SQLite database into the image at build time -- not
# generated at container startup -- so the running container's data is
# immutable, per _docs/outdated/architecture.md §4.3. Writes to
# apps/api/data/eligibility.db (the path db.py/seed.py define, #3),
# which resolves to /app/data/eligibility.db in this image.
RUN python seed.py

EXPOSE 8080

# Cloud Run convention: listen on $PORT, defaulting to 8080 if unset.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
