FROM python:3.8-slim

# RUN apt-get update && apt-get install -y unixodbc-dev gcc g++ libspatialindex-dev python-rtree curl zip

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY CVs ./CVs
COPY schemas ./schemas
COPY mongodb_initialize.py ./

CMD ["python", "-u", "mongodb_initialize.py"]
