"""Workshop 2 - Recherche et enrichissement d'adresses BANO.

Deux modes de recherche, comme decrit dans l'article Elastic
"Enriching Your Postal Addresses With the Elastic Stack - Part 2":
  1. Recherche par nom (numero + nom de rue)
  2. Recherche geospatiale (point GPS + rayon)

Interroge l'alias "bano" (qui pointe vers l'index bano-25).
"""
import os
from pathlib import Path

from elasticsearch import Elasticsearch
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / "elastic-start-local" / ".env"
load_dotenv(ENV_PATH)

ES_URL = os.getenv("ES_LOCAL_URL", "http://localhost:9200")
API_KEY = os.getenv("ES_LOCAL_API_KEY")

ALIAS = "bano"


def get_client() -> Elasticsearch:
    return Elasticsearch(ES_URL, api_key=API_KEY)


def search_by_name(client: Elasticsearch, numero: str, rue: str, commune: str | None = None, size: int = 5):
    """Recherche une adresse par numero + nom de rue (correspondance textuelle)."""
    should = [
        {"match": {"numero": numero}},
        {"match": {"rue": rue}},
    ]
    query = {"bool": {"should": should, "minimum_should_match": 1}}

    if commune:
        query = {
            "bool": {
                "should": should,
                "minimum_should_match": 1,
                "filter": [{"term": {"commune.keyword": commune}}],
            }
        }

    resp = client.search(index=ALIAS, size=size, query=query)
    return [h["_source"] for h in resp["hits"]["hits"]]


def search_by_geo(client: Elasticsearch, lat: float, lon: float, radius: str = "500m", size: int = 5):
    """Trouve les adresses les plus proches d'un point GPS, triees par distance."""
    resp = client.search(
        index=ALIAS,
        size=size,
        query={
            "bool": {
                "filter": {
                    "geo_distance": {
                        "distance": radius,
                        "location": {"lat": lat, "lon": lon},
                    }
                }
            }
        },
        sort=[
            {
                "_geo_distance": {
                    "location": {"lat": lat, "lon": lon},
                    "order": "asc",
                    "unit": "m",
                }
            }
        ],
    )
    results = []
    for h in resp["hits"]["hits"]:
        doc = h["_source"]
        doc["_distance_m"] = h["sort"][0]
        results.append(doc)
    return results


def main():
    client = get_client()

    print("=== Recherche par nom : '10 Rue Abraham Louis Breguet' a Besancon ===")
    for addr in search_by_name(client, numero="10", rue="Abraham Louis Breguet", commune="Besançon"):
        print(addr)

    print("\n=== Recherche geo : adresses a moins de 300m du centre de Besancon (47.2378, 6.0241) ===")
    for addr in search_by_geo(client, lat=47.2378, lon=6.0241, radius="300m"):
        print(f"{addr['_distance_m']:.0f}m -> {addr['numero']} {addr['rue']}, {addr['commune']}")


if __name__ == "__main__":
    main()
