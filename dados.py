import pandas as pd
import numpy as np

# Número máximo de amostras
num_samples = 10000

# Carregar dados do arquivo amazon_products.csv
df = pd.read_csv('amazon_products.csv')

# Filtrar as colunas relevantes e remover linhas com valores ausentes
df = df[['asin', 'reviews', 'boughtInLastMonth', 'stars']].dropna()

# Amostragem aleatória para não exceder o número máximo de amostras
df_sampled = df.sample(n=num_samples, random_state=42)

# Criar dados fictícios para query_id
df_sampled['query_id'] = np.random.randint(1, 50, size=num_samples)

# Criar doc_id com base no índice do DataFrame
df_sampled['doc_id'] = df_sampled.index

# Renomear colunas para os nomes das features
df_sampled.rename(columns={'reviews': 'feature1', 'boughtInLastMonth': 'feature2', 'stars': 'relevance'}, inplace=True)

# Arredondar a coluna 'relevance' para inteiros
df_sampled['relevance'] = df_sampled['relevance'].round().astype(int)

# Salvar como CSV
df_sampled.to_csv('training_data_ficticio.csv', index=False)
