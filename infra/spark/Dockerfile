FROM apache/spark:4.0.2

USER root

COPY init/*.sh /opt/spark/init/

ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.13/4.0.2/spark-sql-kafka-0-10_2.13-4.0.2.jar /opt/spark/jars/spark-sql-kafka-0-10_2.13-4.0.2.jar
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.13/4.0.2/spark-token-provider-kafka-0-10_2.13-4.0.2.jar /opt/spark/jars/spark-token-provider-kafka-0-10_2.13-4.0.2.jar
ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.9.0/kafka-clients-3.9.0.jar /opt/spark/jars/kafka-clients-3.9.0.jar
ADD https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.12.1/commons-pool2-2.12.1.jar /opt/spark/jars/commons-pool2-2.12.1.jar
ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar /opt/spark/jars/hadoop-aws-3.4.1.jar
ADD https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar /opt/spark/jars/bundle-2.29.52.jar

RUN chmod +x /opt/spark/init/*.sh \
    && chmod 644 /opt/spark/jars/*.jar

USER spark