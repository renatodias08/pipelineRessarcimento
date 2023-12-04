from airflow import DAG
from airflow.decorators import task
from airflow.operators.bash import BashOperator

from airflow.operators.trigger_dagrun import TriggerDagRunOperator
import json
import requests
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
from pydantic import BaseModel
from typing import Optional
import psycopg2
import boto3
import gzip
import logging
import brotli
from aiokafka import AIOKafkaConsumer
from retrying import retry


# A DAG represents a workflow, a collection of tasks
with DAG(dag_id="AN_NLP_PythonOperator", start_date=datetime(2022, 1, 1), schedule="*/3000 * * * * *") as dag:

    # Tasks are represented as operators
    dag = BashOperator(task_id="processo_arquivos_raw_dag", bash_command="echo processo_arquivos_raw")
    #####################################################################################################################################################################################################################
    class Item(BaseModel):
        descricaoSinistro: Optional[str] = None
        numeroSinistro: Optional[int] = None
        previsao: Optional[str] = None
        probabilidade: Optional[str] = None
        uuid: Optional[str] = None  


    class AnaliseCredito(BaseModel):
        numeroSinistro: int
        status: str
        uuid: str

        
        
    def cadastrar_predicao(item: Item):        
        print("###############cadastrar_predicao#########################")
        print(item.json())

        conn = psycopg2.connect(
            host="postgresql",
            database="postgres",
            user="admin",
            password="admin"
        )
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS analise_predicao (numeroSinistro INTEGER, descricaoSinistro VARCHAR(5000), previsao VARCHAR(255), probabilidade VARCHAR(255), uuid VARCHAR(255), datahora TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        #if result is None:
        cur.execute("INSERT INTO analise_predicao (numeroSinistro, descricaoSinistro, previsao,  probabilidade,  uuid) VALUES (%s, %s, %s, %s, %s)", (item.numeroSinistro, item.descricaoSinistro, item.previsao, item.probabilidade, item.uuid))
        conn.commit()
        cur.execute("SELECT * FROM analise_predicao WHERE uuid = %s ORDER BY datahora DESC LIMIT 1  ", (item.uuid,))
        result = cur.fetchall()
        conn.close()  # close the connection
        response = []
        for row in result:
            response.append({"numeroSinistro": row[0], "descricaoSinistro": row[1], "previsao": row[2], "probabilidade": row[3], "uuid": row[4], "dataHora": row[3]})


    def decompress(file_bytes: bytes) -> str:
        file_encoding = "utf-8" # replace with your desired encoding
        return str(
            brotli.decompress(file_bytes),
            file_encoding,
        )

    def cadastrar_dados(analiseCredito: AnaliseCredito):

        try:
            response = cadastrar_credito(analiseCredito)
        except requests.exceptions.HTTPError as err:
            print(f"Erro HTTP: {err}")
            print(err.response.status_code)
            print(err.response.text)
        except requests.exceptions.ConnectionError as err:
            print(f"Erro de conexão: {err}")
        except requests.exceptions.Timeout as err:
            print(f"Erro de tempo limite: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Erro desconhecido: {err}")

            
    def cadastrar_credito(analiseCredito: AnaliseCredito):
        print("###############cadastrar_credito#########################")
        print(analiseCredito.json())        
        conn = psycopg2.connect(
            host="postgresql",
            database="postgres",
            user="admin",
            password="admin"
        )
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS analise_credito (numeroSinistro INTEGER, status VARCHAR(255), uuid VARCHAR(255), datahora TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("INSERT INTO analise_credito (numeroSinistro, status, uuid) VALUES (%s, %s, %s)", (int(analiseCredito.numeroSinistro), analiseCredito.status, analiseCredito.uuid))
        conn.commit()
        cur.execute("SELECT * FROM analise_credito WHERE uuid = %s ORDER BY datahora DESC LIMIT 1 ", (analiseCredito.uuid,))
        result = cur.fetchall()
        conn.close()  # close the connection
        response = []
        for row in result:
            response.append({"numeroSinistro": row[0], "status": row[1], "uuid": row[2], "dataHora": row[3]})
        print("###############cadastrar_credito_response#########################")
        return response        
    #####################################################################################################################################################################################################################


    def check_bucket_connection():
        s3_client = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minio', aws_secret_access_key='minio123')
        bucket_name = 'ressarcimento'
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print("Connection successful!")
        except:
            print("Connection failed.")

    def copiar_arquivio(payload, bucket_name, file_name, new_file_name):    
        try:
            ###################################copiar_arquivio RAW###############################################################################
            s3_client = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minio', aws_secret_access_key='minio123')
            bucket_name = 'ressarcimento'

            source = '/CONTEXT/'+new_file_name       
            # Copy object A as object B with a new prefix
            copy_source = {
                'Bucket': bucket_name,
                'Key': '/RAW/' + file_name
            }
            ###################################predict-ressarcimento inicio###############################################################################


            objeto = json.loads(payload)
            descricaoSinistro = objeto["descricaoSinistro"]
            numeroSinistro = objeto["numeroSinistro"]


            url = 'http://fastapiapp:8000/v1/predict-ressarcimento'
            headers = {'Content-Type': 'application/json'}
            data = {'descricaoSinistro': descricaoSinistro}
            print("###############IINICIO V4########################")
            response_data = requests.post(url, headers=headers, json=data)
            response =  response_data.json()
            print(response_data)
            print("###############FIM V4########################")
        

        ## Verificar a resposta da API
            payload_predicao_response = payload  
            payload_predicao_json = json.loads(payload_predicao_response)    
            payload_predicao_json["previsao"] = response['previsao']        
            payload_predicao_json["probabilidade"] = response['probabilidade']        


            # Acessa os valores dos atributos usando as chaves
            descricaoSinistro = payload_predicao_json["descricaoSinistro"]
            numeroSinistro = payload_predicao_json["numeroSinistro"]
            uuid = payload_predicao_json["uuid"]
            status = payload_predicao_json["status"]
            previsao = payload_predicao_json["previsao"]
            probabilidade = payload_predicao_json["probabilidade"]

            item = Item(descricaoSinistro = descricaoSinistro, numeroSinistro = numeroSinistro, previsao = previsao, probabilidade = probabilidade, uuid =uuid)

            cadastrar_predicao(item)

        ####################################predict-ressarcimento fim #########################################################################################       

            payload_predicao_response = json.dumps(payload_predicao_json)
            s3_client.put_object(Bucket=bucket_name, Key=source, Body=payload_predicao_response) 
            print(f"Arquivo {file_name} foi copiado para pasta :{source}")
            s3_client.copy_object(CopySource=copy_source, Bucket=bucket_name, Key='/RAW/RAW_' + new_file_name)
            print(f"Arquivo {file_name} foi renomeado para :'/RAW/RAW_' + {new_file_name}")
            s3_client.delete_object(Bucket=bucket_name, Key='/RAW/' + file_name)
            print(f"Arquivo {file_name} foi deletado da pasta : +'/RAW/' + {file_name}")

        except requests.exceptions.HTTPError as err:
            print(f"Erro HTTP: {err}")
            print(err.response.status_code)
            print(err.response.text)
        except requests.exceptions.ConnectionError as err:
            print(f"Erro de conexão: {err}")
        except requests.exceptions.Timeout as err:
            print(f"Erro de tempo limite: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Erro desconhecido: {err}")   


    @task()
    def process_files():
        s3_client = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minio', aws_secret_access_key='minio123')
        bucket_name = 'ressarcimento'
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='RAW/')
        json_object = {}

        for content in response['Contents']:       
            obj = s3_client.get_object(Bucket=bucket_name, Key=content['Key'])
            try:
                strJson = decompress(bytes(obj['Body'].read()))
                json_object = json.loads(strJson)
                file_name = content['Key'].split('/')[-1]
                    
                    
                if 'numeroSinistro' in json_object and "RAW_" not in file_name:
                    #print(f'###############Processando o arquivo {file_name}#########################')
                    if json_object['numeroSinistro'] % 2 == 0:
                        status = "ADIMPLENTE"
                    else:
                        status = "INADIMPLENTE"
                    json_object["status"] = status
                    new_json_object = json.dumps(json_object).replace("'", "\"")

                    analiseCredito = AnaliseCredito(numeroSinistro = json_object['numeroSinistro'], status = json_object['status'], uuid = json_object['uuid'])

                    cadastrar_dados(analiseCredito)
                    print("#####################analiseCredito##############################################")
                    print(analiseCredito.json())

                    new_file_name = json_object['uuid'] + '.json'
                    copiar_arquivio(new_json_object, bucket_name, file_name, new_file_name)

                    print(f"Arquivo {content['Key']} com valor da chave 'descricaoSinistro' é: {json_object['descricaoSinistro']}")
                    print(f"Arquivo {content['Key']} com json  é: {json_object}")
                else:
                    print(f'-->Arquivo ja processado {file_name} \n conteudo {strJson}')        

            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar a string JSON: {e}")

        print('All files downloaded and deleted successfully!')

    dag >> process_files()