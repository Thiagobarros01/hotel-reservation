FROM python:3.9-slim

WORKDIR /app

COPY ./app /app

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port","8001"]