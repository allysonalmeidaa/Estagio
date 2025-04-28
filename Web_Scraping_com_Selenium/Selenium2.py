# Importando as bibliotecas necessárias
from selenium import webdriver  # Principal biblioteca para automação do navegador
from selenium.webdriver.common.by import By  # Classe para definir método de localização de elementos
from selenium.webdriver.chrome.service import Service  # Gerencia o serviço do ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait  # Permite esperar elementos carregarem
from selenium.webdriver.support import expected_conditions as EC  # Condições para espera de elementos
from webdriver_manager.chrome import ChromeDriverManager  # Gerencia instalação do ChromeDriver
import pandas as pd  # Biblioteca para manipulação de dados
import os  # Biblioteca para operações com sistema de arquivos


def extrair_dados_livros():
    navegador = None
    try:
        # Configuração e início do Chrome
        servico = Service(ChromeDriverManager().install())  # Configura o serviço do ChromeDriver
        navegador = webdriver.Chrome(service=servico)  # Inicia o navegador Chrome
        wait = WebDriverWait(navegador, 10)  # Configura espera de até 10 segundos
        
        # Acessando o site
        print("\nIniciando extração de dados...")
        navegador.get('https://books.toscrape.com/')  # Acessa o site
        # Espera e encontra todos os elementos de livros
        livros = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'product_pod')))
        
        dados = []  # Lista para armazenar dados dos livros
        
        # Extraindo dados de cada livro
        for livro in livros:
            try:
                # Coletando dados básicos (título e preço)
                titulo = livro.find_element(By.CSS_SELECTOR, 'h3 a').get_attribute('title')
                preco = float(livro.find_element(By.CLASS_NAME, 'price_color').text.replace('£', ''))
                
                # Entrando na página do livro para pegar quantidade
                livro.find_element(By.CSS_SELECTOR, 'h3 a').click()
                # Extrai a quantidade disponível
                quantidade = int(wait.until(EC.presence_of_element_located(
                    (By.CLASS_NAME, 'instock'))).text.replace('In stock (', '').replace(' available)', ''))
                navegador.back()  # Volta para página anterior
                # Espera elementos carregarem novamente
                wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'product_pod')))
                
                # Adiciona dados do livro à lista
                dados.append({
                    'Título': titulo,
                    'Preço (£)': preco,
                    'Quantidade': quantidade
                })
                
            except Exception as e:
                continue  # Se houver erro, continua com próximo livro
        
        # Cria DataFrame e ordena por preço
        return pd.DataFrame(dados).sort_values(by='Preço (£)')
        
    finally:
        # Garante que o navegador será fechado
        if navegador:
            navegador.quit()

def mostrar_resumo(df, arquivo):
    # Limpa o terminal (cls para Windows, clear para Unix)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Formata e mostra cabeçalho da tabela
    print("\n=== PRIMEIROS 5 LIVROS ENCONTRADOS ===")
    print("\n{:<60} {:>10} {:>12}".format("TÍTULO", "PREÇO (£)", "QUANTIDADE"))
    print("-" * 84)  # Linha separadora
    
    # Mostra dados dos 5 primeiros livros
    for _, livro in df.head().iterrows():
        # Trunca títulos longos
        titulo = livro['Título'][:57] + "..." if len(livro['Título']) > 57 else livro['Título']
        # Formata e exibe dados do livro
        print("{:<60} £{:>9.2f} {:>12}".format(
            titulo,
            livro['Preço (£)'],
            livro['Quantidade']
        ))
    
    # Exibe estatísticas e informações finais
    print("\n" + "=" * 84)
    print("\nESTATÍSTICAS:")
    print(f"Total de livros cadastrados: {len(df)}")
    print(f"Total de livros em estoque: {df['Quantidade'].sum()}")
    print(f"\nDados salvos em: {arquivo}")

def main():
    try:
        # Extrai dados e salva em Excel
        df = extrair_dados_livros()
        # Define caminho do arquivo de saída
        arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'livros.xlsx')
        df.to_excel(arquivo, index=False)  # Salva DataFrame em Excel
        
        # Exibe resumo formatado
        mostrar_resumo(df, arquivo)
        
    except Exception as erro:
        print(f"Erro: {erro}")

# Verifica se é o arquivo principal sendo executado
if __name__ == "__main__":
    main()