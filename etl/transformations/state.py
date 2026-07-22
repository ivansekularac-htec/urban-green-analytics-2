"""
Helpers for managing ETL processing state stored in MinIO.
"""

import json

from pyspark.sql import SparkSession


def get_watermark(
    spark: SparkSession,
    path: str,
) -> str | None:
    """
    Read the last processed batch watermark from MinIO.
    """

    jvm = spark.sparkContext._jvm
    conf = spark.sparkContext._jsc.hadoopConfiguration()

    uri = jvm.java.net.URI(path)

    fs = jvm.org.apache.hadoop.fs.FileSystem.get(
        uri,
        conf,
    )

    file_path = jvm.org.apache.hadoop.fs.Path(path)

    if not fs.exists(file_path):
        return None

    input_stream = fs.open(file_path)

    reader = jvm.java.io.BufferedReader(jvm.java.io.InputStreamReader(input_stream))

    content = []

    line = reader.readLine()

    while line:
        content.append(line)
        line = reader.readLine()

    reader.close()

    state = json.loads("".join(content))

    return state.get("last_batch")


def set_watermark(
    spark: SparkSession,
    path: str,
    batch: str,
) -> None:
    """
    Write the last processed batch watermark to MinIO.
    """

    jvm = spark.sparkContext._jvm
    conf = spark.sparkContext._jsc.hadoopConfiguration()

    uri = jvm.java.net.URI(path)

    fs = jvm.org.apache.hadoop.fs.FileSystem.get(
        uri,
        conf,
    )

    file_path = jvm.org.apache.hadoop.fs.Path(path)

    state = {
        "last_batch": batch,
    }

    content = json.dumps(
        state,
        indent=2,
    )

    output_stream = fs.create(
        file_path,
        True,
    )

    output_stream.write(
        bytearray(
            content,
            "UTF-8",
        )
    )

    output_stream.close()
