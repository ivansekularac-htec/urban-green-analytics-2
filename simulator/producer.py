"""Sensor data simulator: publishes synthetic readings to Kafka.

On first start (sentinel absent), emits a historical backfill with no outliers,
then enters an infinite live loop emitting readings every
SIMULATOR_LIVE_INTERVAL_SECONDS.

The 75 farms x 6 sensor types = 450 farm_sensors are seeded deterministically
by Postgres init SQL (infra/postgres/sql/03_seeds.sql); their IDs and the
(farm_id, sensor_type_id) mapping never change, so they're hardcoded here and
the simulator has no runtime Postgres dependency.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError

if TYPE_CHECKING:
    from collections.abc import Iterator

log = logging.getLogger("simulator")

# (id, name, unit, gen_min, gen_max). gen_* drive value generation. For most
# types they match the API validation bounds in app.sensor_types, but Energy
# Usage's DB ceiling of 1_000_000 kWh is just a non-null placeholder, not an
# operating envelope -- here it's narrowed to a realistic per-10-min draw.
SENSOR_TYPES: list[dict] = [
    {
        "id": 1,
        "name": "Temperature",
        "unit": "C",
        "gen_min": 18.0,
        "gen_max": 25.0,
    },
    {
        "id": 2,
        "name": "Humidity",
        "unit": "%",
        "gen_min": 50.0,
        "gen_max": 70.0,
    },
    {
        "id": 3,
        "name": "Light Intensity",
        "unit": "PPFD",
        "gen_min": 200.0,
        "gen_max": 800.0,
    },
    {"id": 4, "name": "pH Level", "unit": "pH", "gen_min": 5.0, "gen_max": 7.0},
    {"id": 5, "name": "Energy Usage", "unit": "kWh", "gen_min": 40.0, "gen_max": 80.0},
    {
        "id": 6,
        "name": "CO2 Concentration",
        "unit": "ppm",
        "gen_min": 400.0,
        "gen_max": 1200.0,
    },
]

NUM_FARMS = 75
SENSORS_PER_FARM = len(SENSOR_TYPES)
TOTAL_SENSORS = NUM_FARMS * SENSORS_PER_FARM  # 450

STATE_PATH = Path("/state/.bootstrapped")


@dataclass
class Config:
    bootstrap: str
    topic: str
    backfill_days: int
    backfill_events_per_day: int
    live_interval_seconds: int
    outlier_probability: float
    log_level: str


def load_config() -> Config:
    return Config(
        bootstrap=os.environ.get("SIMULATOR_KAFKA_BOOTSTRAP", "urbangreen-kafka:9092"),
        topic=os.environ.get("KAFKA_TOPIC_SENSOR_READINGS", "sensor_readings"),
        backfill_days=int(os.environ.get("SIMULATOR_BACKFILL_DAYS", "365")),
        backfill_events_per_day=int(
            os.environ.get("SIMULATOR_BACKFILL_EVENTS_PER_DAY", "4")
        ),
        live_interval_seconds=int(
            os.environ.get("SIMULATOR_LIVE_INTERVAL_SECONDS", "600")
        ),
        outlier_probability=float(
            os.environ.get("SIMULATOR_OUTLIER_PROBABILITY", "0.01")
        ),
        log_level=os.environ.get("SIMULATOR_LOG_LEVEL", "INFO").upper(),
    )


def iter_farm_sensors() -> Iterator[tuple[int, int, int, dict]]:
    """Yield (farm_sensor_id, farm_id, sensor_type_id, sensor_type) for all 450 sensors.

    Order matches the seed SQL: CROSS JOIN generate_series(1,75) f, generate_series(1,6) s.
    """
    for farm_id in range(1, NUM_FARMS + 1):
        for sensor_type in SENSOR_TYPES:
            sensor_type_id = sensor_type["id"]
            farm_sensor_id = (farm_id - 1) * SENSORS_PER_FARM + sensor_type_id
            yield farm_sensor_id, farm_id, sensor_type_id, sensor_type


def generate_value(
    sensor_type: dict,
    when: datetime,
    rng: random.Random,
    outlier_prob: float,
) -> float:
    gmin = sensor_type["gen_min"]
    gmax = sensor_type["gen_max"]
    half = (gmax - gmin) / 2.0
    mid = (gmin + gmax) / 2.0
    amp = 0.30 * half
    sigma = 0.05 * half
    seconds_of_day = when.hour * 3600 + when.minute * 60 + when.second
    cycle = math.sin(2 * math.pi * seconds_of_day / 86400.0)
    value = mid + amp * cycle + rng.gauss(0.0, sigma)
    value = max(gmin, min(gmax, value))
    if outlier_prob > 0.0 and rng.random() < outlier_prob:
        value = value * (1.0 + rng.choice((-0.20, 0.20)))
    return round(value, 3)


def build_event(
    farm_sensor_id: int,
    farm_id: int,
    sensor_type_id: int,
    value: float,
    when: datetime,
) -> dict:
    return {
        "farm_sensor_id": farm_sensor_id,
        "farm_id": farm_id,
        "sensor_type_id": sensor_type_id,
        "value": value,
        "timestamp": int(when.timestamp()),
    }


def make_producer(bootstrap: str, deadline_seconds: int = 60) -> KafkaProducer:
    deadline = time.monotonic() + deadline_seconds
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return KafkaProducer(
                bootstrap_servers=bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8"),
                acks=1,
                linger_ms=50,
                batch_size=64 * 1024,
                retries=5,
                retry_backoff_ms=500,
            )
        except KafkaTimeoutError as exc:
            last_err = exc
            log.warning(f"kafka broker not yet reachable at {bootstrap}; retrying...")
            time.sleep(2.0)
    raise RuntimeError(f"kafka broker unreachable at {bootstrap}: {last_err}")


def send_event(producer: KafkaProducer, topic: str, event: dict) -> None:
    producer.send(topic, key=event["farm_sensor_id"], value=event)


def run_backfill(producer: KafkaProducer, cfg: Config, rng: random.Random) -> None:
    if STATE_PATH.exists():
        log.info(f"sentinel {STATE_PATH} found; skipping historical backfill")
        return

    total_events = cfg.backfill_days * cfg.backfill_events_per_day * TOTAL_SENSORS
    log.info(
        f"starting backfill: {cfg.backfill_days} days x "
        f"{cfg.backfill_events_per_day} events/day x "
        f"{TOTAL_SENSORS} sensors = {total_events} events"
    )

    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now - timedelta(days=cfg.backfill_days)
    interval_seconds = 86400 // cfg.backfill_events_per_day
    sensors = list(iter_farm_sensors())

    sent = 0
    log_every = 50_000
    for day_idx in range(cfg.backfill_days):
        day_start = start + timedelta(days=day_idx)
        for tick_idx in range(cfg.backfill_events_per_day):
            when = day_start + timedelta(seconds=tick_idx * interval_seconds)
            for fs_id, farm_id, st_id, st in sensors:
                value = generate_value(st, when, rng, outlier_prob=0.0)
                send_event(
                    producer, cfg.topic, build_event(fs_id, farm_id, st_id, value, when)
                )
                sent += 1
                if sent % log_every == 0:
                    pct = sent * 100.0 / total_events
                    log.info(f"backfill progress: {sent} / {total_events} ({pct:.1f}%)")

    producer.flush()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.touch()
    log.info(f"backfill complete: {sent} events flushed; sentinel written")


def run_live(producer: KafkaProducer, cfg: Config, rng: random.Random) -> None:
    log.info(
        f"entering live loop: {TOTAL_SENSORS} sensors every "
        f"{cfg.live_interval_seconds} seconds (outlier prob={cfg.outlier_probability:.3f})"
    )
    while True:
        when = datetime.now(timezone.utc).replace(microsecond=0)
        for fs_id, farm_id, st_id, st in iter_farm_sensors():
            value = generate_value(st, when, rng, outlier_prob=cfg.outlier_probability)
            send_event(
                producer, cfg.topic, build_event(fs_id, farm_id, st_id, value, when)
            )
        producer.flush()
        log.info(f"live tick emitted at {when.isoformat()} ({TOTAL_SENSORS} events)")
        time.sleep(cfg.live_interval_seconds)


def main() -> None:
    cfg = load_config()
    logging.basicConfig(
        level=cfg.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    log.info(f"simulator starting; bootstrap={cfg.bootstrap} topic={cfg.topic}")
    rng = random.Random()
    producer = make_producer(cfg.bootstrap)
    try:
        run_backfill(producer, cfg, rng)
        run_live(producer, cfg, rng)
    except KeyboardInterrupt:
        log.info("interrupted; closing producer")
    finally:
        producer.close(timeout=10)


if __name__ == "__main__":
    main()
