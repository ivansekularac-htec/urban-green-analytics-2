-- =============================================================================
-- Database: urbangreen_db
-- Purpose:
--   Main ClickHouse data warehouse database for Urban Green Analytics.
--
-- Description:
--   This database contains the dimensional model (star schema) used for
--   production analytics, sensor monitoring, sustainability reporting,
--   and operational dashboards.
--
-- Layers:
--   - Dimensions: descriptive entities (farms, crops, sensors, users, dates)
--   - Facts: atomic business events (harvests and sensor readings)
--   - Aggregates: pre-computed daily metrics for dashboard performance
--
-- Initialization:
--   This script is executed during the first ClickHouse container startup
--   through /docker-entrypoint-initdb.d.
--
-- Dependencies:
--   None. This database must be created before loading tables.
-- =============================================================================


CREATE DATABASE IF NOT EXISTS urbangreen_db;

USE urbangreen_db;