#!/bin/bash
# wait-for-db.sh

echo "Waiting for MySQL to be ready..."

while ! mysqladmin ping -h "db" -u"user" -p"password" --silent; do
  sleep 2
done

echo "MySQL is ready. Starting backend..."
exec "$@"
