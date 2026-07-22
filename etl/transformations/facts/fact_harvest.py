"""
Load fact_harvests incrementally into ClickHouse.
"""

from transformations.common import (
    create_spark,
    # write_clickhouse,
)
from transformations.state import (
    get_watermark,
    # set_watermark,
)

WATERMARK_PATH = "s3a://staging/_checkpoints/spark/fact_harvests/watermark.json"

SOURCE_PATH = "s3a://staging/raw/postgres/harvests/"


def main():

    spark = create_spark("fact_harvests")

    last_batch = get_watermark(
        spark,
        WATERMARK_PATH,
    )

    # read new batches

    # transform

    # write ClickHouse

    # update watermark


if __name__ == "__main__":
    main()
