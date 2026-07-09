FROM jupyter/base-notebook:python-3.11

USER root

# Install Java (required by Spark)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure JAVA_HOME
RUN JAVA_PATH=$(dirname "$(dirname "$(readlink -f "$(which java)")")") && \
    ln -s "${JAVA_PATH}" /usr/lib/jvm/default-java

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER jovyan

# Python packages
RUN pip install --no-cache-dir \
    pyspark==4.0.2 \
    pandas \
    pyarrow 

WORKDIR /home/jovyan/work

EXPOSE 8888 4040

ENTRYPOINT [ \
    "start-notebook.sh", \
    "--ServerApp.token=", \
    "--ServerApp.password=", \
    "--ServerApp.disable_check_xsrf=True", \
    "--ServerApp.ip=0.0.0.0", \
    "--ServerApp.allow_origin=*" \
    ]
