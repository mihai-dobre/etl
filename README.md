# etl

## Commands:
* Create a postgres user: `docker-compose run db psql -h db -p 5432 -U postgres --command "CREATE USER yieldify WITH PASSWORD 'yieldify';CREATE DATABASE etl OWNER yieldify;GRANT ALL PRIVILEGES ON DATABASE etl TO yieldify;"`
