#!/bin/bash
set -e

# Replace environment variables with their values
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create user
    CREATE USER ${PG_APP_USERNAME} WITH PASSWORD '${PG_APP_PASSWORD}';
    
    -- Create database
    CREATE DATABASE ${PG_APP_DATABASE};
    
    -- Grant all privileges on database to user
    GRANT ALL PRIVILEGES ON DATABASE ${PG_APP_DATABASE} TO ${PG_APP_USERNAME};
    
    -- Connect to the new database and grant schema privileges
    \c ${PG_APP_DATABASE}
    
    -- Grant schema privileges
    GRANT ALL ON SCHEMA public TO ${PG_APP_USERNAME};
EOSQL
