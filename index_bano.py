"""Index the BANO dataset (department 25) into Elasticsearch."""
import csv
import os
from pathlib import Path

from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / "elastic-start-local" / ".env"
load_dotenv(ENV_PATH)

ES_URL = os.getenv("ES_LOCAL_URL", "http://localhost:9200")
API_KEY = os.getenv("ES_LOCAL_API_KEY")

INDEX_NAME = "bano-25"
CSV_PATH = Path(__file__).parent / "data" / "bano-25.csv"

COLUMNS = ["id", "numero", "rue", "code_postal", "commune", "source", "lat", "lon"]

MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "numero": {"type": "keyword"},
            "rue": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "code_postal": {"type": "keyword"},
            "commune": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "source": {"type": "keyword"},
            "location": {"type": "geo_point"},
        }
    }
}


def read_rows():
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != len(COLUMNS):
                continue
            doc = dict(zip(COLUMNS, row))
            try:
                lat = float(doc.pop("lat"))
                lon = float(doc.pop("lon"))
            except ValueError:
                continue
            doc["location"] = {"lat": lat, "lon": lon}
            yield {"_index": INDEX_NAME, "_id": doc["id"], "_source": doc}


def main():
    client = Elasticsearch(ES_URL, api_key=API_KEY)
    print(client.info())

    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
    client.indices.create(index=INDEX_NAME, body=MAPPING)

    success, errors = helpers.bulk(client, read_rows(), chunk_size=2000, raise_on_error=False)
    print(f"Indexed: {success} documents, errors: {len(errors) if errors else 0}")

    client.indices.refresh(index=INDEX_NAME)
    count = client.count(index=INDEX_NAME)
    print(f"Total documents in index '{INDEX_NAME}': {count['count']}")


if __name__ == "__main__":
    main()
