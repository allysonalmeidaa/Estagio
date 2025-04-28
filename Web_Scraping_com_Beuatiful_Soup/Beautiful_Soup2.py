# 1. Importação das bibliotecas necessárias
from bs4 import BeautifulSoup  # Biblioteca para extrair dados de HTML
import requests  # Biblioteca para fazer requisições web
import pandas as pd  # Biblioteca para manipulação de dados em formato tabular
import os  # Biblioteca para operações com sistema de arquivos

# 2. Configurações básicas
url = 'https://books.toscrape.com/'  # URL do site que vamos extrair os dados
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135.0.0.0'}
# Headers simula um navegador web para evitar bloqueios do site

try:
    # 3. Fazendo a requisição HTTP e verificando se foi bem sucedida
    pagina = requests.get(url, headers=headers)
    # Faz uma requisição GET para a URL especificada
    
    if pagina.status_code != 200:
        # Verifica se a requisição foi bem sucedida (código 200)
        print(f"Erro na requisição: {pagina.status_code}")
        exit()
    
    # 4. Criando o objeto BeautifulSoup para análise do HTML
    sopa = BeautifulSoup(pagina.content, 'html.parser')
    # Cria um objeto BeautifulSoup que permite navegar pelo HTML da página
    
    # 5. Encontrando todos os livros na página
    livros = sopa.find_all('article', class_='product_pod')
    # Localiza todos os elementos 'article' que contêm informações dos livros

    # 6. Coletando dados dos livros usando list comprehension
    dados_livros = {
        'Título': [livro.h3.a['title'] for livro in livros],
        # Extrai o título de cada livro do atributo 'title' da tag 'a' dentro de 'h3'
        
        'Preço (£)': [float(livro.find('p', class_='price_color').text.replace('£', '')) for livro in livros],
        # Extrai o preço, remove o símbolo '£' e converte para float
        
        'Classificação': [livro.p['class'][1] for livro in livros],
        # Extrai a classificação (rating) do livro
        
        'Disponibilidade': [livro.find('p', class_='instock').text.strip() for livro in livros]
        # Extrai a informação de disponibilidade do livro
    }

    # 7. Criando e organizando o DataFrame
    df = pd.DataFrame(dados_livros)
    # Cria um DataFrame pandas com os dados coletados
    
    df = df.sort_values(by='Preço (£)')
    # Ordena o DataFrame pelo preço em ordem crescente
    
    # 8. Definindo o caminho e salvando o arquivo Excel
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'livros_encontrados.xlsx')
    # os.path.abspath(__file__): obtém o caminho absoluto do script atual
    # os.path.dirname(): obtém o diretório do script
    # os.path.join(): combina o caminho do diretório com o nome do arquivo
    
    df.to_excel(caminho_arquivo, index=False, sheet_name='Livros')
    # Salva o DataFrame em um arquivo Excel
    # index=False: não inclui o índice do DataFrame
    # sheet_name='Livros': nome da planilha no arquivo Excel
    
    # 9. Exibindo o resumo dos dados coletados
    print(f"\nTotal de livros encontrados: {len(df)}")
    print(f"Arquivo salvo em: {caminho_arquivo}")
    print("\nPrimeiros 5 livros encontrados:")
    
    # 10. Iterando pelos primeiros 5 livros para mostrar detalhes
    for i, livro in df.head().iterrows():
        # df.head(): retorna os primeiros 5 registros
        # iterrows(): permite iterar pelas linhas do DataFrame
        print(f"\nLivro {i+1}:")
        print(f"Título: {livro['Título']}")
        print(f"Preço: £{livro['Preço (£)']}")
        print(f"Classificação: {livro['Classificação']}")
        print(f"Disponibilidade: {livro['Disponibilidade']}")
        print("-" * 50)

# 11. Tratamento de erros
except Exception as erro:
    print(f"Ocorreu um erro: {str(erro)}")
    # Captura e exibe qualquer erro que ocorra durante a execução do código