FROM apache/airflow:3.1.1-python3.10

# Add ps utility to Docker image
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-jre-headless \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

COPY requirements.txt /requirements.txt

# Keep the Airflow version fixed while installing additional providers
RUN pip install --no-cache-dir \
    "apache-airflow==3.1.1" \
    -r /requirements.txt

# Driver-side dependencies for reading from MinIO through S3A
ADD --chmod=0644 \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar \
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/hadoop-aws-3.4.1.jar

ADD --chmod=0644 \
    https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar \
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/bundle-2.29.52.jar

# Driver-side dependency for writing DataFrames to ClickHouse through JDBC
ADD --chmod=0644 \
    https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.9.8/clickhouse-jdbc-0.9.8-all-dependencies.jar \
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/clickhouse-jdbc-0.9.8-all-dependencies.jar