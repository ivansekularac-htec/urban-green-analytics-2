#!/bin/sh
set -e

MASTER="spark://urbangreen-spark-master:7077"
ROOT="/opt/airflow/spark-jobs"

submit() {
    echo
    echo "===================================================="
    echo "Running: $1"
    echo "===================================================="

    spark-submit \
        --master "$MASTER" \
        --deploy-mode client \
        "$ROOT/$1"
}

echo
echo "========== LOADING DIMENSIONS =========="

submit "dimensions/load_dim_crop.py"
submit "dimensions/load_dim_quality_grade.py"
submit "dimensions/load_dim_farm.py"
submit "dimensions/load_dim_sensor_type.py"
submit "dimensions/load_dim_sensor.py"
submit "dimensions/load_dim_role.py"
submit "dimensions/load_dim_user.py"
submit "dimensions/load_dim_user_farm_role.py"

echo
echo "========== LOADING FACTS =========="

submit "facts/load_fact_harvests.py"
submit "facts/load_fact_sensor_readings.py"

echo
echo "========== LOADING AGGREGATES =========="

submit "aggregates/load_fact_daily_farm_metrics.py"
submit "aggregates/load_fact_daily_farm_quality_metrics.py"
submit "aggregates/load_fact_daily_sensor_metrics.py"
submit "aggregates/load_fact_farm_leaderboard.py"

echo
echo "========================================"
echo "Warehouse load completed successfully."
echo "========================================"