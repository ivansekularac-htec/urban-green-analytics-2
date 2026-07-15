-- =============================================================================
-- Urban Green Analytics - ClickHouse warehouse init (1/4)
-- Ticket: T3.1.2 - Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Creates the analytical database. All subsequent init scripts run against it.
--
-- Execution:
--   Runs once on first container start, while /var/lib/clickhouse is empty.
--   Init SQL cannot read environment variables, so the database name is fixed
--   here as `urbangreen` and MUST match CLICKHOUSE_DB in docker-compose / .env
--   (the image entrypoint creates that database too). Rename in both places.
--
-- Dependencies: none (runs first).
-- =============================================================================

CREATE DATABASE IF NOT EXISTS urbangreen;

USE urbangreen;
