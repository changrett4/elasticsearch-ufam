import lightgbm as lgb
import pandas as pd
import numpy as np

# Carregar dados de treinamento fictícios
df = pd.read_csv('training_data_ficticio.csv')

# Ordenar dados por query_id para garantir que os dados estejam agrupados corretamente
df = df.sort_values(by='query_id')

# Extrair grupos
query_ids = df['query_id'].values
unique_query_ids, query_id_counts = np.unique(query_ids, return_counts=True)

# Preparar dados para LightGBM
features = df[['feature1', 'feature2']].values
relevance = df['relevance'].values

# Definir parâmetros do LightGBM
params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [1, 3, 5],
    'boosting_type': 'gbdt',
    'min_data_in_leaf': 1,  # Ajustar para permitir menor número de dados em cada folha
    'min_data_in_bin': 1    # Ajustar para permitir menor número de dados em cada bin
}

# Criar dataset do LightGBM
train_data = lgb.Dataset(features, label=relevance, group=query_id_counts.tolist())

# Treinar o modelo
model = lgb.train(params, train_data, num_boost_round=100)

# Salvar o modelo treinado
model.save_model('lambdamart_model.txt')
