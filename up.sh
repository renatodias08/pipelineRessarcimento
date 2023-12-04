#!/bin/bash
   #service docker stop
   #rm ~/.docker/config.json
   #service docker start

    docker-compose -f docker-compose-kafka.yml up  -d 
    docker-compose -f docker-compose-nifi.yml up  -d 
    docker-compose -f docker-compose-airflow.yml up  -d 

   docker logs jupyter
   


