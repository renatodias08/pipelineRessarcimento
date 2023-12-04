FROM apache/airflow:2.7.0  AS  airflow

USER root

RUN apt -y update && \
    apt install -y --no-install-recommends 
        # dependência para o ambiente de desenvolvimento
         #git && \
    # clean
     #apt clean && \
     #rm -rf /var/lib/apt/lists/* && \
     #rm -r /tmp/*

USER airflow

WORKDIR /opt

COPY ./requirements.txt /opt
#COPY ./plugins/framework-dataflow/dist/framework_dataflow-0.0.0-py3-none-any.whl /opt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install retrying  && \
    pip install brotli  && \
    pip install aiokafka  && \
    pip install operators  && \
    pip install requests  && \
    pip install timedelta  && \
    pip install datetime  && \
    pip install --no-cache-dir minio  && \
    pip install pip install boto3  && \
    pip install pip install numpy  && \
    pip install -r requirements.txt