#!/bin/bash
   #service docker stop
   #rm ~/.docker/config.json
   #service docker start
    docker-compose -f docker-compose-kafka.yml up  -d --build
    docker-compose -f docker-compose-nifi.yml up  -d --build
    docker-compose -f docker-compose-airflow.yml up  -d --build

   docker logs jupyter

   #Criar a rede
   docker network create pipeline-data-net
   #Conectar os containes
   docker network connect pipeline-data-net minio/minio:latest
   docker network connect pipeline-data-net  pipelineressarcimento_airflow-webserver_1
   docker network connect pipeline-data-net  pipelineressarcimento_fastapiapp_1
   docker network connect pipeline-data-net  zookeeper
   docker network connect pipeline-data-net  pipelineressarcimento_producer_1
   docker network connect pipeline-data-net  pipelineressarcimento_consumer_1
   docker network connect pipeline-data-net pipelineressarcimento_kafka_1
   docker network connect pipeline-data-net pipelineressarcimento_zookeeper_kafka_1
   docker network connect pipeline-data-net  pipelineressarcimento_pgadmin_1
   docker network connect pipeline-data-net  jupyter
   docker network connect pipeline-data-net pipelineressarcimento_superset_1
   docker network connect pipeline-data-net pipelineressarcimento_postgres_1
   docker network connect pipeline-data-net pipelineressarcimento_minio_1
      


