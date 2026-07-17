FROM apache/airflow:3.1.1-python3.10

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps default-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java \
    PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

USER root
ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/
ADD https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/
ADD https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.9.8/clickhouse-jdbc-0.9.8-all-dependencies.jar /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/
RUN chmod 644 \
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/hadoop-aws-3.4.1.jar \
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/bundle-2.29.52.jar \
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/jars/clickhouse-jdbc-0.9.8-all-dependencies.jar

USER airflow