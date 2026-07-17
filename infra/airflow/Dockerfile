FROM apache/airflow:3.1.1-python3.10

# JVM (spark-submit needs it) + ps (Spark's load-spark-env.sh shells out to ps)
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps default-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# spark-submit needs JAVA_HOME; default-java is an arch-agnostic alternatives symlink
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

# Driver-side JARs mirroring the cluster image for the remote sources the driver
# loads (MinIO/S3 read + ClickHouse write). pyspark's install dir is $SPARK_HOME
# when launched via pip. Kafka JARs are not needed (streaming runs in the cluster).
ADD --chown=airflow:0 --chmod=644 https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/
ADD --chown=airflow:0 --chmod=644 https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/
ADD --chown=airflow:0 --chmod=644 https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.9.8/clickhouse-jdbc-0.9.8-all-dependencies.jar /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/
