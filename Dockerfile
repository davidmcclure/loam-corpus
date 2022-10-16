
FROM python:3.10

ARG CODE_DIR=/code
WORKDIR $CODE_DIR

# Java
RUN apt-get update && apt-get install -y openjdk-11-jre
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64

# Spark
ARG SPARK_URL=https://dlcdn.apache.org/spark/spark-3.3.0/spark-3.3.0-bin-hadoop3.tgz
ENV SPARK_HOME=/opt/spark
ENV PATH $PATH:${SPARK_HOME}/bin
RUN curl -sL --retry 3 $SPARK_URL | gunzip | tar x -C /opt/ \
  && mv /opt/spark-* $SPARK_HOME \
  && chown -R root:root $SPARK_HOME

# Install Poetry.
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH=$PATH:/root/.local/bin
RUN poetry config virtualenvs.create false

# Install dependencies.
ADD pyproject.toml poetry.lock $CODE_DIR/
RUN poetry install

# Install the module.
ADD . $CODE_DIR
RUN poetry install

# Download tokenizer data.
RUN python -m nltk.downloader punkt

ENV PYSPARK_DRIVER_PYTHON=ipython