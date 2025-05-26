FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Install MySQL client (for wait-for-db.sh)
RUN apt-get update && apt-get install -y default-mysql-client

COPY . .

# Start using wait script (optional, if not using CMD in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
