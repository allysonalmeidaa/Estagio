import pandas as pd
import sqlite3
import os

# Obter o diretório atual onde o código está sendo executado
current_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho para o arquivo Excel
excel_path = r"C:\Programação_estágio\Sql\livros.xlsx"

# Caminho para o banco de dados (será criado no mesmo diretório do script)
db_path = os.path.join(current_dir, 'Banco_livros_Excel.db')

# Ler os dados da planilha Excel
dados_excel = pd.read_excel(excel_path, engine="openpyxl")

# Conectar ao banco de dados SQLite
conexao = sqlite3.connect(db_path)
cursor = conexao.cursor()

# Criar a tabela no banco de dados com restrição de unicidade
cursor.execute('''
CREATE TABLE IF NOT EXISTS livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL UNIQUE,
    preco REAL NOT NULL,
    quantidade INTEGER NOT NULL,
    avaliacao INTEGER NOT NULL
)
''')

# Inserir os dados do Excel no banco de dados
for index, linha in dados_excel.iterrows():
    titulo = linha['Título']
    preco = linha['Preço (£)']
    quantidade = linha['Quantidade']
    avaliacao = linha['Avaliação']

    # Ignorar linhas com dados inválidos
    if pd.isna(titulo) or titulo.strip() == "" or pd.isna(preco) or pd.isna(quantidade) or pd.isna(avaliacao):
        print(f"Linha ignorada: {linha}")
        continue

    # Usar INSERT OR IGNORE para evitar duplicação
    cursor.execute('''
    INSERT OR IGNORE INTO livros (titulo, preco, quantidade, avaliacao) VALUES (?, ?, ?, ?)
    ''', (titulo, preco, quantidade, avaliacao))

# Salvar e fechar a conexão
conexao.commit()
conexao.close()

print(f"Dados importados com sucesso! Banco de dados criado em: {db_path}")