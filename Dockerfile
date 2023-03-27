FROM python:3.10

WORKDIR /rebuild_wchat
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3","rebuild_chat.py"]