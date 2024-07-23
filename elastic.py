from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
import pandas as pd
from elasticsearch.helpers import bulk
import lightgbm as lgb
import numpy as np

app = Flask(__name__)
CORS(app)

# Conectar ao Elasticsearch
es = Elasticsearch("http://localhost:9200")
model = lgb.Booster(model_file='lambdamart_model.txt')

# Leitura do arquivo CSV
df = pd.read_csv("amazon_products.csv")

# Remoção de linhas com valores ausentes
df = df.dropna()
columns_to_drop = ['productURL', 'asin', 'listPrice']
df.drop(columns_to_drop, axis=1, inplace=True)

# Obter o número de linhas do DataFrame
num_rows = df.shape[0]
features_columns = ['reviews', 'boughtInLastMonth']
# Definir o tamanho da amostra como o menor valor entre 20000 e o total de linhas
sample_size = min(20000, num_rows)

# Amostragem do DataFrame e reset dos índices
df = df.sample(sample_size, random_state=42).reset_index(drop=True)

index_name = "products"

# Definição das configurações e mapeamento do índice
settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "my_custom_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "my_custom_analyzer"
            },
            "stars": {
                "type": "float"
            },
            "reviews": {
                "type": "integer"
            },
            "price": {
                "type": "float"
            },
            "categoryName": {
                "type": "text",
                "analyzer": "my_custom_analyzer"
            },
            "isBestSeller": {
                "type": "integer"
            },
            "boughtInLastMonth": {
                "type": "integer"
            },
            "imgUrl": {
                "type": "text"
            }
        }
    }
}

# Criação do índice com as configurações e mapeamento definidos
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=settings)

# Inserção de dados no Elasticsearch
bulk_data = []
for i, row in df.iterrows():
    doc = row.to_dict()
    
    titulo = doc['title']
    first_term = titulo.split()[0]
    doc["first_term"] = first_term

    doc['isBestSeller'] = 1 if doc['isBestSeller'] else 0

    bulk_data.append(
        {
            "_index": index_name,
            "_id": i,
            "_source": doc
        }
    )
bulk(es, bulk_data)

# Refresh índice para garantir que todos os documentos sejam pesquisáveis
es.indices.refresh(index="products")

@app.route('/search', methods=['GET'])
def search():
    # Obtendo o parâmetro de busca da URL
    query = request.args.get('q', '')
    first = query.split()[0]

    # Construindo cláusula de match_phrase para termos exatos
    must_matches = [{"match": {"first_term": {"query": first, "boost": 5000}}},
        {"match": {"title": {"query": query, "boost": 1000}}}]

    # Construindo cláusula de match para categoria
    should_matches = [{"match": {"categoryName": query}}]

    # Realizar a busca no Elasticsearch
    resp = es.search(
        index='products',
        query={
            "bool": {
                "must": must_matches,
                "should": should_matches
            }
        },
        size=10
    )

    # Obter os documentos
    hits = [hit['_source'] for hit in resp['hits']['hits']]

    # Criar um DataFrame com os documentos retornados
    docs_df = pd.DataFrame(hits)

    # Extrair features dos documentos
    docs_features = docs_df[features_columns].values

    # Classificar documentos com o modelo LambdaMART
    scores = model.predict(docs_features)
    docs_df['score'] = scores

    # Ordenar documentos com base nas previsões
    sorted_docs = docs_df.sort_values(by='score', ascending=False)

    # Retornar os resultados classificados
    results = sorted_docs.to_dict(orient='records')

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
