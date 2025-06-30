FROM python:3.11-slim

WORKDIR /app

# Crea user non-root per sicurezza
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/uploads/players && \
    chown -R appuser:appuser /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

# Cambia all'utente non-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]