FROM jupyter/base-notebook:latest

USER root

RUN apt-get update && apt-get install -y openjdk-17-jre-headless && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN JAVA_PATH=$(readlink -f $(which java) | sed 's:/bin/java::') && \
    echo "export JAVA_HOME=$JAVA_PATH" >> /etc/profile.d/java.sh && \
    ln -s $JAVA_PATH /usr/lib/jvm/default-java

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER jovyan

RUN pip install --no-cache-dir \
    pyspark==4.0.2 \
    pandas \
    pyarrow

RUN mkdir -p /opt/conda/lib/python3.*/site-packages/pyspark/jars

USER root

# Add the same jars as Spark image
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.13/4.0.2/spark-sql-kafka-0-10_2.13-4.0.2.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

ADD https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.13/4.0.2/spark-token-provider-kafka-0-10_2.13-4.0.2.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.9.0/kafka-clients-3.9.0.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

ADD https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.12.1/commons-pool2-2.12.1.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

ADD https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

ADD https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.9.8/clickhouse-jdbc-0.9.8-all-dependencies.jar \
    /opt/conda/lib/python3.11/site-packages/pyspark/jars/

RUN chmod 644 /opt/conda/lib/python3.*/site-packages/pyspark/jars/*.jar


USER jovyan

WORKDIR /home/jovyan/work

EXPOSE 8888 4040

ENTRYPOINT ["start-notebook.sh", \
            "--ServerApp.token=", \
            "--ServerApp.password=", \
            "--ServerApp.disable_check_xsrf=True", \
            "--ServerApp.ip=0.0.0.0", \
            "--ServerApp.allow_origin=*"]