FROM python:3.11.11-slim

WORKDIR /app

# Copiar requirements primeiro (cache de layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
