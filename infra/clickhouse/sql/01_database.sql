-- =============================================================================
-- Urban Green Analytics — ClickHouse warehouse init (1/4)
-- Ticket: T3.1.2 — Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Creates the analytical database used by the OLAP layer. All subsequent
--   init scripts run against this database.
--
-- Execution:
--   Runs on first container start when /var/lib/clickhouse is empty.
--   Database name is fixed here as urbangreen_analytics. It MUST match
--   CLICKHOUSE_DB in docker-compose / .env (entrypoint creates that DB too).
--   Init SQL cannot read env vars — if you rename the warehouse, update both.
--
-- Dependencies: none (runs first, alphabetically after any 01_* peers).
-- =============================================================================
CREATE DATABASE IF NOT EXISTS urbangreen_analytics;

USE urbangreen_analytics;