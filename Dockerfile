FROM python:3.8

# RUN apt-get update && apt-get install -y unixodbc-dev gcc g++ libspatialindex-dev python-rtree curl zip

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY mongodb_initialize.py ./

CMD ["python", "mongodb_initialize.py", "parameters.yml"]
