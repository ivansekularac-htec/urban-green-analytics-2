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
--   Runs automatically on first container start when /var/lib/clickhouse is
--   empty (docker-entrypoint-initdb.d). Requires CLICKHOUSE_DB in .env
--   (default: urbangreen_analytics).
--
-- Dependencies: none (runs first, alphabetically after any 01_* peers).
-- =============================================================================
CREATE DATABASE IF NOT EXISTS urbangreen_analytics;

USE urbangreen_analytics;