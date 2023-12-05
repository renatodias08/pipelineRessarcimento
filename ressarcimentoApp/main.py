from fastapi import FastAPI


## text preprocessing modules
from string import punctuation
from nltk.tokenize import word_tokenize
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re  
import os
from os.path import dirname, join, realpath
import joblib
from pydantic import BaseModel
from typing import Optional
import psycopg2
import boto3
import gzip
import json
import logging
import brotli
from aiokafka import AIOKafkaConsumer
from retrying import retry
import requests

app = FastAPI(
    title="API de Ressarcimento Sinistro Automóvel",
    description="Busca de ressarcimento do sinistro. Probabilidade de um sinistro ser ressarcível",
    version="0.1",
)

# load the sentiment model

with open(
    join(dirname(realpath(__file__)), "models/sentiment_model_pipeline.pkl"), "rb"
) as f:
    model = joblib.load(f)


# cleaning the data
def text_cleaning(text, remove_stop_words=True, lemmatize_words=True):
    # Clean the text, with the option to remove stop_words and to lemmatize word

    # Clean the text
    text = re.sub(r"[^A-Za-z0-9]", " ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"http\S+", " link ", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\s+", "", text)  # remove numbers

    # Remove punctuation from text
    text = "".join([c for c in text if c not in punctuation])

    # Optionally, remove stop words
    if remove_stop_words:

        # load stopwords
        stop_words = stopwords.words("english")
        text = text.split()
        text = [w for w in text if not w in stop_words]
        text = " ".join(text)

    # Optionally, shorten words to their stems
    if lemmatize_words:
        text = text.split()
        lemmatizer = WordNetLemmatizer()
        lemmatized_words = [lemmatizer.lemmatize(word) for word in text]
        text = " ".join(lemmatized_words)

    # Return a list of words
    return text


class Item(BaseModel):
    descricaoSinistro: Optional[str] = None
    numeroSinistro: Optional[int] = None
    previsao: Optional[str] = None
    probabilidade: Optional[str] = None
    uuid: Optional[str] = None


@app.post("/v1/predict-ressarcimento")
def predict_ressarcimento(item: Item):
    """
    Busca de ressarcimento do sinistroProbabilidade de um sinistro ser ressarcível
    :param Item:
    :return: previsao, probabilidades
    """
    # clean the review
    #cleaned_review = text_cleaning(item.descricaoSinistro)
    cleaned_review = item.descricaoSinistro

    # perform previsao
    previsao = model.predict([cleaned_review])
    output = int(previsao[0])
    probas = model.predict_proba([cleaned_review])
    output_probability = "{:.2f}".format(float(probas[:, output]))

    # output dictionary
    sentiments = {0: "RESSARCIVEL", 1: "NAO_RESSARCIVEL"}

    # show results
    result = {"previsao": sentiments[output], "probabilidade": output_probability}

    return result

#####################################################################################################################################################################################################################

class AnaliseCredito(BaseModel):
    numeroSinistro: int
    status: str
    uuid: str

@app.post("/v1/analise-credito")
async def analisar_credito(analiseCredito: AnaliseCredito):

    """
    Analisar Crédito
    """
    response = cadastrar_credito(analiseCredito)

    return {"message": "Registro inserido com sucesso!", "analiseCredito": response}



def cadastrar_credito(analiseCredito: AnaliseCredito):

    print("###############cadastrar_credito#########################")
   # print(analiseCredito.json())
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
    #print(response.json())
    return response

#####################################################################################################################################################################################################################


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
    print(response)



########################################################################################################################

@app.get("/v1/analise-ressarcimento/{uuid}")
def obter_predicao(uuid: str):   
    """
    Obter Predicao
    """     
    print("###############obter_predicao#########################")
    print(uuid)

    conn = psycopg2.connect(
        host="postgresql",
        database="postgres",
        user="admin",
        password="admin"
    )
    cur = conn.cursor()
    cur.execute("SELECT numerosinistro, descricaosinistro, previsao, probabilidade, uuid, TO_CHAR(datahora, 'DD-MM-YYYY HH24:MI:SS') AS datahora_formatada FROM analise_predicao WHERE uuid = %s ORDER BY datahora DESC LIMIT 1  ", (uuid,))
    result = cur.fetchall()

    previsaoResponse = []
    numeroSinistro=""
    for row in result:
        numeroSinistro = row[0]
        previsaoResponse.append({ "descricaoSinistro": row[1], "status": row[2], "probabilidade": row[3],"dataHora": row[5]})


    cur.execute("SELECT numerosinistro, status, uuid, TO_CHAR(datahora, 'DD-MM-YYYY HH24:MI:SS') AS datahora_formatada FROM analise_credito WHERE uuid = %s ORDER BY datahora DESC LIMIT 1 ", (uuid,))
    result = cur.fetchall()
    conn.close()  # close the connection
    analiseCreditoResponse = []

    for row in result:
        analiseCreditoResponse.append({ "status": row[1], "dataHora": row[3]})



    return {"message": "Registro obtido com sucesso!",
    "uuid": uuid, 
    "numeroSinistro": numeroSinistro, 
    "analiseCredito": analiseCreditoResponse, 
    "analiseRessarciemnto": previsaoResponse
    }
