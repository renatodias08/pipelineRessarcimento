from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.email_operator import EmailOperator
from airflow.sensors.filesystem import FileSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import json
import os
import boto3
import brotli
from retrying import retry
import requests



default_args = {
        'depends_on_past' : False,
        'email' : ['ged@gmail.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries' : 1,
        'retry_delay' : timedelta(seconds=10)
        }

dag = DAG('RessarcivelPythonOperator', description='Dados da Sinistro',
          schedule_interval=timedelta(minutes=1),  # Executar a cada 5 minutos
          start_date=datetime(2023,3,5),
          catchup=False, default_args=default_args, default_view='graph',
          doc_md="## Dag para registrar dados de sinistro")

group_check_temp = TaskGroup("group_check_temp", dag=dag)

def process_file(**kwarg):
    s3_client = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minio', aws_secret_access_key='minio123')
    bucket_name = 'ressarcimento'
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='CONTEXT/')
    json_object = {}

    for content in response['Contents']:
        print(content['Key'])
        obj = s3_client.get_object(Bucket=bucket_name, Key=content['Key'])
        file_name = content['Key'].split('/')[-1]
        if 'CONTEXT_' not in file_name:
            try:
            # Ler o conteúdo do arquivo como bytes
                data = obj['Body'].read()
                # Decodificar os bytes para uma string usando UTF-8
                data = data.decode("utf-8")
                # Converter a string em um objeto Python usando json.loads
                data = json.loads(data)
                # Imprimir o objeto Python formatado como JSON
                print(json.dumps(data, indent=4))
        
                kwarg['ti'].xcom_push(key='uuid',value=data['uuid'])
                kwarg['ti'].xcom_push(key='descricaoSinistro',value=data['descricaoSinistro'])
                kwarg['ti'].xcom_push(key='numeroSinistro',value=data['numeroSinistro'])
                kwarg['ti'].xcom_push(key='status',value=data['status'])
                kwarg['ti'].xcom_push(key='previsao',value=data['previsao'])
                kwarg['ti'].xcom_push(key='probabilidade',value=data['probabilidade'])
                
                source = '/CONTEXT/'+file_name       
                # Copy object A as object B with a new prefix
                copy_source = {
                    'Bucket': bucket_name,
                    'Key': '/CONTEXT/' + file_name
                }
                s3_client.copy_object(CopySource=copy_source, Bucket=bucket_name, Key='/TRUST/' + file_name)
                print(f"Arquivo {file_name} foi copiado para :'/TRUST/' + {file_name}")

                s3_client.copy_object(CopySource=copy_source, Bucket=bucket_name, Key='/CONTEXT/CONTEXT_' + file_name)
                print(f"Arquivo {file_name} foi renomeado para :'/CONTEXT/CONTEXT_' + {file_name}")
                s3_client.delete_object(Bucket=bucket_name, Key='/CONTEXT/' + file_name)
                print(f"Arquivo {file_name} foi deletado da pasta : +'/CONTEXT/' + {file_name}")
            except json.JSONDecodeError as err:
                print(f"Erro ao decodificar a string JSON: {err}")
                print(err.response.status_code)
                print(err.response.text)
            except requests.exceptions.HTTPError as err:
                print(f"Erro HTTP: {err}")
                print(err.response.status_code)
                print(err.response.text)
            except requests.exceptions.ConnectionError as err:
                print(f"Erro de conexão: {err}")
                print(err.response.status_code)
                print(err.response.text)
            except requests.exceptions.Timeout as err:
                print(f"Erro de tempo limite: {err}")
                print(err.response.status_code)
                print(err.response.text)
            except requests.exceptions.RequestException as err:
                print(f"Erro desconhecido: {err}")   
                print(err.response.status_code)
                print(err.response.text)


get_data = PythonOperator(
            task_id = 'get_data',
            python_callable= process_file, 
            provide_context = True,
            dag=dag)

send_email_alert = EmailOperator(
    task_id='send_email_alert',
    to='ged@gmail.com',
    subject='Airflow alert',
    html_content='''<h3>Sinistro ressarcivel Uuid: {{ ti.xcom_pull(task_ids='get_data', key='uuid') }}</h3>
                    <p>Dag: RessarcivelNLP</p>
                      <ol>
                        <li>Descricao do Sinistro: {{ ti.xcom_pull(task_ids='get_data', key='descricaoSinistro') }}</li>
                        <li>Numero do Sinistro: {{ ti.xcom_pull(task_ids='get_data', key='numeroSinistro') }}</li>
                        <li>Analise de Credito: {{ ti.xcom_pull(task_ids='get_data', key='status') }}</li>
                        <li>Previsao: {{ ti.xcom_pull(task_ids='get_data', key='previsao') }}</li>
                        <li>Probabilidade: {{ ti.xcom_pull(task_ids='get_data', key='probabilidade') }}</li>
                        <li>Uuid: {{ ti.xcom_pull(task_ids='get_data', key='uuid') }}</li>
                    </ol>
                    ''',
    task_group=group_check_temp,
    dag=dag
)

send_email_normal = EmailOperator(
    task_id='send_email_normal',
    to='ged@gmail.com',
    subject='Airflow advise',
    html_content='''<h3>Sinistro nao ressarcivel Uuid: {{ ti.xcom_pull(task_ids='get_data', key='uuid') }}</h3>
                    <p>Dag: RessarcivelNLP </p>
                        <ol>
                            <li>Descricao do Sinistro: {{ ti.xcom_pull(task_ids='get_data', key='descricaoSinistro') }}</li>
                            <li>Numero do Sinistro: {{ ti.xcom_pull(task_ids='get_data', key='numeroSinistro') }}</li>
                            <li>Analise de Credito: {{ ti.xcom_pull(task_ids='get_data', key='status') }}</li>
                            <li>Previsao: {{ ti.xcom_pull(task_ids='get_data', key='previsao') }}</li>
                            <li>Probabilidade: {{ ti.xcom_pull(task_ids='get_data', key='probabilidade') }}</li>
                            <li>Uuid: {{ ti.xcom_pull(task_ids='get_data', key='uuid') }}</li>
                        </ol>
                    ''',
    task_group=group_check_temp,
    dag=dag
)

def avalia_temp(**context):
    previsao =  context['ti'].xcom_pull(task_ids='get_data', key="previsao")
    descricaoSinistro =  context['ti'].xcom_pull(task_ids='get_data', key="descricaoSinistro")
    numeroSinistro =  context['ti'].xcom_pull(task_ids='get_data', key="numeroSinistro")
    status =  context['ti'].xcom_pull(task_ids='get_data', key="status")
    probabilidade =  context['ti'].xcom_pull(task_ids='get_data', key="probabilidade")
    
    if previsao is not None and previsao != '':
        if previsao == 'SIM':
            return 'group_check_temp.send_email_alert'
        else:
            return 'group_check_temp.send_email_normal'
        
                        

check_temp_branc = BranchPythonOperator(
                                task_id = 'check_temp_branc',
                                python_callable=avalia_temp,
                                provide_context = True,
                                dag = dag,
                                task_group = group_check_temp)

with group_check_temp:
    check_temp_branc >> [send_email_alert, send_email_normal]

get_data >> group_check_temp


