# Importando bibliotecas necessárias
from playwright.sync_api import sync_playwright  # Principal biblioteca para automação web
import pandas as pd  # Para manipulação de dados
import os  # Para operações com sistema de arquivos
import time  # Para operações relacionadas a tempo

def extrair_dados_livros():
    # Inicializa variáveis como None para garantir fechamento adequado
    playwright = None
    browser = None
    
    try:
        print("\nIniciando extração de dados...")
        playwright = sync_playwright().start()  # Inicia o Playwright
        
        # Configura e inicia o navegador
        browser = playwright.chromium.launch(headless=False)  # Inicia navegador visível
        context = browser.new_context()  # Cria contexto isolado
        page = context.new_page()  # Cria nova página
        page.set_default_timeout(30000)  # Define timeout de 30 segundos
        
        # Navega até o site
        page.goto('https://books.toscrape.com/')
        
        # Aguarda carregamento dos elementos dos livros
        page.wait_for_selector('.product_pod')
        
        dados = []  # Lista para armazenar dados dos livros
        
        # Extrai links e títulos de todos os livros usando JavaScript
        livros_links = page.eval_on_selector_all('.product_pod h3 a', """
            (elements) => elements.map(element => ({
                title: element.getAttribute('title'),
                href: element.href
            }))
        """)
        
        # Processa cada livro encontrado
        for livro_info in livros_links:
            try:
                # Navega para página do livro
                page.goto(livro_info['href'])
                page.wait_for_selector('.price_color')  # Espera preço carregar
                page.wait_for_selector('.instock')  # Espera estoque carregar
                
                # Extrai preço e quantidade
                preco = float(page.query_selector('.price_color').inner_text().replace('£', ''))
                texto_estoque = page.query_selector('.instock').inner_text()
                quantidade = int(texto_estoque.replace('In stock (', '').replace(' available)', ''))
                
                # Adiciona dados à lista
                dados.append({
                    'Título': livro_info['title'],
                    'Preço (£)': preco,
                    'Quantidade': quantidade
                })
                
                # Retorna à página principal
                page.goto('https://books.toscrape.com/')
                page.wait_for_selector('.product_pod')
                
            except Exception as e:
                print(f"Erro ao processar livro {livro_info['title']}: {str(e)}")
                continue
        
        # Cria DataFrame e ordena por preço
        return pd.DataFrame(dados).sort_values(by='Preço (£)')
        
    finally:
        # Garante fechamento dos recursos
        if browser:
            browser.close()
        if playwright:
            playwright.stop()

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