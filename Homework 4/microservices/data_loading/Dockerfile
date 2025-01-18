FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5005

CMD ["python", "data_loading.py"]