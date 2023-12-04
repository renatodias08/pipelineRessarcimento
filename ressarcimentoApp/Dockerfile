FROM python:3.8-slim

WORKDIR /app/
ADD requirements.txt /app/

RUN pip install -r requirements.txt
RUN  pip install -U scikit-learn
RUN pip install psycopg2-binary

RUN pip install retrying
RUN pip install brotli
RUN pip install aiokafka
RUN pip install boto3
RUN pip install requests
RUN pip install numpy
ADD . /app/

EXPOSE 8005

CMD ["hypercorn", "./ressarcimentoApp/main:app", "-b", "0.0.0.0:8000", "--reload"]