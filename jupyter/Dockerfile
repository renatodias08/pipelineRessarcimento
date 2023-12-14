# Use uma imagem base do Jupyter (por exemplo, jupyter/scipy-notebook)
FROM jupyter/scipy-notebook

# Copie os arquivos necessários para o contêiner (por exemplo, requirements.txt, dados, notebooks)
COPY requirements.txt /requirements.txt
#COPY my_data.csv /my_data.csv
#COPY my_jupyter.ipynb /my_jupyter.ipynb

# Instale as dependências (se houver) a partir do requirements.txt
RUN pip install -r /requirements.txt
RUN pip install pymongo
RUN pip install python-dotenv
RUN pip install folium
RUN pip install -U scikit-learn
#RUN pip install psycopg2-binary
RUN pip install retrying
RUN pip install brotli
RUN pip install aiokafka
RUN pip install boto3
RUN pip install requests
RUN pip install pydantic
RUN pip install boto3

RUN pip install keras
RUN pip install -U tensorflow
RUN pip install -U numpy
# Exponha a porta 8888 (a porta padrão do Jupyter)
EXPOSE 8888

# Defina o ponto de entrada para iniciar o Jupyter Lab
ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root"]
