FROM python:3.12-slim

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/app/

CMD ["python", "main.py"]