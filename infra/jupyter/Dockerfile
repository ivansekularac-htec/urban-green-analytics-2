FROM jupyter/base-notebook:latest

USER root

RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Auto-detect JAVA_HOME regardless of architecture
RUN JAVA_PATH=$(readlink -f $(which java) | sed 's:/bin/java::') && \
    echo "export JAVA_HOME=$JAVA_PATH" >> /etc/profile.d/java.sh && \
    ln -s "$JAVA_PATH" /usr/lib/jvm/default-java

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER jovyan

RUN pip install --no-cache-dir \
    pyspark==4.0.2 \
    pandas \
    pyarrow

WORKDIR /home/jovyan/work

EXPOSE 8888 4040

ENTRYPOINT ["start-notebook.sh", \
    "--ServerApp.token=", \
    "--ServerApp.password=", \
    "--ServerApp.disable_check_xsrf=True", \
    "--ServerApp.ip=0.0.0.0", \
    "--ServerApp.allow_origin=*"]