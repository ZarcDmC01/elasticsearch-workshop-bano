# ElasticSearch – Story 1 : Recherche d'adresses postales via la stack Elastic

Brief individuel (GRETA / Simplon) visant à prendre en main la stack Elastic (Elasticsearch + Kibana) en local, sur le dataset **BANO** (Base Adresses Nationale Ouverte), en remplacement d'une API existante basée sur des requêtes SQL.

## Sommaire

- [Contexte](#contexte)
- [Workshop 1 — Installer Elasticsearch et Kibana via Docker](#workshop-1--installer-elasticsearch-et-kibana-via-docker)
- [Workshop 2 — Indexer et interroger le dataset BANO](#workshop-2--indexer-et-interroger-le-dataset-bano)
- [Structure du dépôt](#structure-du-dépôt)
- [Prérequis](#prérequis)
- [Marche à suivre complète](#marche-à-suivre-complète)
- [Exemples de requêtes](#exemples-de-requêtes)
- [Aller plus loin](#aller-plus-loin)

## Contexte

Le logiciel de supervision urbaine de l'entreprise dispose d'une API de recherche d'adresses postales interrogeant une base MsSQL en SQL. L'équipe souhaite évaluer une alternative : **Elasticsearch**, moteur de recherche NoSQL basé sur Apache Lucene, plus adapté à la recherche textuelle floue et à l'analyse de gros volumes de données.

Le dataset utilisé est **BANO** (initiative OpenStreetMap France), restreint au **département 25 (Doubs)** pour les tests.

## Workshop 1 — Installer Elasticsearch et Kibana via Docker

Objectif : avoir un cluster Elasticsearch + Kibana fonctionnel en local, sans passer par Elastic Cloud.

### Étapes

1. **Installer Docker Desktop** (prérequis, avec WSL2 activé sous Windows).
2. **Lancer le script officiel `start-local`** :
   ```bash
   curl -fsSL https://elastic.co/start-local | sh
   ```
3. Le script crée un dossier `elastic-start-local/` contenant :
   - un `docker-compose` préconfiguré (2 services : `es-local-dev`, `kibana-local-dev`)
   - un fichier `.env` avec les identifiants générés (mot de passe `elastic`, clé API)
4. Vérifier que les conteneurs tournent :
   ```bash
   docker ps
   ```
5. Tester la connexion à l'API :
   ```bash
   source elastic-start-local/.env
   curl $ES_LOCAL_URL -H "Authorization: ApiKey ${ES_LOCAL_API_KEY}"
   ```

### Accès

| Service | URL | Identifiants |
|---|---|---|
| Elasticsearch | http://localhost:9200 | ApiKey (voir `.env`) ou Basic Auth `elastic` / mot de passe (voir `.env`) |
| Kibana | http://localhost:5601 | `elastic` / mot de passe (voir `.env`) |

⚠️ Le fichier `elastic-start-local/.env` contient des secrets (mot de passe + clé API) : il est volontairement exclu du dépôt Git (`.gitignore`). Il est régénéré localement à chaque installation.

## Workshop 2 — Indexer et interroger le dataset BANO

Objectif : charger un vrai dataset d'adresses postales et démontrer les capacités de recherche/agrégation d'Elasticsearch.

### Étapes

1. **Télécharger le dataset BANO** du département 25 :
   ```bash
   curl -fsSL https://bano.openstreetmap.fr/data/bano-25.csv -o data/bano-25.csv
   ```
   Format CSV (sans en-tête) : `id, numero, rue, code_postal, commune, source, lat, lon`
2. **Créer un environnement Python** et installer les dépendances :
   ```bash
   python -m venv venv
   source venv/Scripts/activate   # Windows (Git Bash)
   pip install elasticsearch python-dotenv requests
   ```
3. **Indexer le dataset** avec un mapping dédié (`geo_point` pour les coordonnées, sous-champs `.keyword` pour les agrégations) :
   ```bash
   python index_bano.py
   ```
4. **Interroger l'index** : recherche par nom, recherche géospatiale, agrégations :
   ```bash
   python search_bano.py
   ```
5. **Créer un alias** `bano` pointant vers l'index `bano-25` (prépare une organisation multi-départements, un index par département + un alias global) :
   ```bash
   curl -X POST "$ES_LOCAL_URL/_aliases" -H "Authorization: ApiKey ${ES_LOCAL_API_KEY}" -H 'Content-Type: application/json' -d '{
     "actions": [{ "add": { "index": "bano-25", "alias": "bano" } }]
   }'
   ```

## Structure du dépôt

```
.
├── README.md                     # ce fichier
├── RER.ipynb                     # Rapport d'Étude et de Recherche
├── index_bano.py                 # indexation du dataset BANO dans Elasticsearch
├── search_bano.py                # requêtes de recherche (nom, géo)
├── data/
│   └── bano-25.csv               # dataset BANO département 25 (Doubs)
├── Workshop_1.md                 # doc d'installation Elasticsearch (README officiel)
├── Workshop_2.md                 # article Elastic Blog "Enriching Postal Addresses - Part 2"
├── Story_1_...[APPRENANT].pdf    # énoncé du brief
├── kibana_tutorial.pdf           # ressource Kibana
└── elasticsearch-sizing-and-capacity-planning-....pdf   # ressource sizing
```

Non versionné (`.gitignore`) : `venv/`, `elastic-start-local/` (secrets), `elasticsearch-main.zip` (code source complet, non nécessaire ici).

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) avec WSL2 (Windows)
- Python 3.10+
- `curl`, `git`, [GitHub CLI](https://cli.github.com/) (optionnel, pour republier)

## Marche à suivre complète

Depuis un poste vierge (Windows + Git Bash) :

```bash
# 1. Lancer Docker Desktop, puis vérifier qu'il répond
docker ps

# 2. Installer Elasticsearch + Kibana en local
curl -fsSL https://elastic.co/start-local | sh

# 3. Créer et activer un environnement Python
python -m venv venv
source venv/Scripts/activate

# 4. Installer les dépendances
pip install elasticsearch python-dotenv requests

# 5. Télécharger le dataset BANO (département 25)
mkdir -p data
curl -fsSL https://bano.openstreetmap.fr/data/bano-25.csv -o data/bano-25.csv

# 6. Indexer les données
python index_bano.py

# 7. Tester les requêtes de recherche
python search_bano.py

# 8. (optionnel) Ouvrir Kibana pour explorer visuellement
#    http://localhost:5601  -> Dev Tools / Discover
```

## Exemples de requêtes

**Recherche textuelle (match) :**
```json
GET bano-25/_search
{
  "query": { "match": { "commune": "Besançon" } }
}
```

**Agrégation (top communes) :**
```json
GET bano-25/_search
{
  "size": 0,
  "aggs": {
    "top_communes": { "terms": { "field": "commune.keyword", "size": 5 } }
  }
}
```

**Recherche géospatiale (adresses à moins de 300m d'un point GPS) :**
```json
GET bano/_search
{
  "query": {
    "bool": {
      "filter": {
        "geo_distance": {
          "distance": "300m",
          "location": { "lat": 47.2378, "lon": 6.0241 }
        }
      }
    }
  },
  "sort": [
    { "_geo_distance": { "location": { "lat": 47.2378, "lon": 6.0241 }, "order": "asc", "unit": "m" } }
  ]
}
```

## Aller plus loin

Pistes non implémentées dans ce dépôt, évoquées dans le RER :

- **Pipeline Logstash** d'enrichissement automatique (routage par département depuis le code postal, filtre `elasticsearch` pour enrichir un flux entrant en continu) — voir Workshop_2.md.
- **Analyzer français** personnalisé sur les champs `rue`/`commune` pour améliorer la tolérance aux fautes d'orthographe et aux accents.
- Extension à l'ensemble des départements français (un index par département + alias `bano` global).
