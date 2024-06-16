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

# Obter o número de linhas do DataFrame
num_rows = df.shape[0]

# Definir o tamanho da amostra como o menor valor entre 10000 e o total de linhas
sample_size = min(10000, num_rows)

# Amostragem do DataFrame e reset dos índices
df = df.sample(sample_size, random_state=42).reset_index(drop=True)

# Inserção de dados no Elasticsearch
bulk_data = []
for i, row in df.iterrows():
    bulk_data.append(
        {
            "_index": "products",
            "_id": i,
            "_source": {        
                "title": row["title"],
            }
        }
    )
bulk(es, bulk_data)

# Refresh índice para garantir que todos os documentos sejam pesquisáveis
es.indices.refresh(index="products")

@app.route('/search', methods=['GET'])
def search():
    # Obtendo o parâmetro de busca da URL
    query = request.args.get('q', '')
    
    # Realizando a busca no Elasticsearch
    resp = es.search(
        index="products",
        query={
            "bool": {
                "must": {
                    "match": {
                        "title": query,
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
