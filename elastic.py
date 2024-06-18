from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
import pandas as pd
from elasticsearch.helpers import bulk

app = Flask(__name__)
CORS(app)
# Conectar ao Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Leitura do arquivo CSV
df = pd.read_csv("amazon_products.csv")

# Remoção de linhas com valores ausentes
df = df.dropna()
columns_to_drop = ['imgUrl', 'productURL','asin','listPrice']
df.drop(columns_to_drop, axis=1, inplace=True)

# Obter o número de linhas do DataFrame
num_rows = df.shape[0]

# Definir o tamanho da amostra como o menor valor entre 10000 e o total de linhas
sample_size = min(10000, num_rows)

# Amostragem do DataFrame e reset dos índices
df = df.sample(sample_size, random_state=42).reset_index(drop=True)

index_name= "products"

# Definição das configurações e mapeamento do índice
settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "my_custom_analyzer": {
                    "type": "custom",
                    "tokenizer": "my_tokenizer",
                    "filter": ["lowercase", "asciifolding"]
                }
            },

            "tokenizer": {
                "my_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 4,
                    "max_gram": 20,
                    "token_chars": [
                        "letter",
                        "digit"
                    ]
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
            "stars": {"type": "float"},
            "reviews": {"type": "integer"},
            "price": {"type": "float"},
            "categoryName": {"type": "text", "analyzer":"my_custom_analyzer"},
            "isBestSeller": {"type": "integer"},
            "boughtInLastMonth": {"type": "integer"}
            # Adicione mais campos aqui conforme necessário
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

    doc['isBestSeller'] = 1 if doc['isBestSeller']  else 0

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
    
    terms = query.split()
    should_matches = []

    # Construindo cláusulas de match para cada termo
    for term in terms:
        should_matches.append( {"match":{"title": term } })
    
    # Realizando a busca no Elasticsearch
    resp = es.search(
        index="products",
        query={
            "function_score":{
            "query": {
                "bool": {
                    "must": should_matches
                }
            },
                    "script_score":{
                    "script":{

                        "source":"(doc['isBestSeller'].value * 20 ) + doc['boughtInLastMonth'].value * 15 + (Math.log(1+doc['reviews'].value)*doc['stars'].value*2) + (1 / ( doc['price'].value + 1)) "
                    }
                },
            },

            
        },
        size=10  
    )
    
    # Formatando o resultado
    results = [hit['_source'] for hit in resp['hits']['hits']]
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
