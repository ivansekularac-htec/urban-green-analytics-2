FROM apache/spark:4.0.2

USER root

COPY init/*.sh /opt/spark/init/

RUN chmod +x /opt/spark/init/*.sh

USER spark