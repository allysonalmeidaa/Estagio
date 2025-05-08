# Importação de bibliotecas necessárias
from playwright.sync_api import sync_playwright  # Automação de navegador para extração de dados
import sqlite3  # Conexão e manipulação do banco de dados SQLite
import os  # Manipulação de caminhos no sistema operacional
import matplotlib.pyplot as plt  # Criação de gráficos
import seaborn as sns  # Visualização de dados, complementando o Matplotlib

# Configuração do caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Playwright_livros_otm.db')

def criar_tabelas_banco():
    """
    Cria as tabelas 'livros' e 'categorias' no banco de dados SQLite.
    """
    # Conexão com o banco de dados
    with sqlite3.connect(DB_PATH) as conexao:
        cursor = conexao.cursor()
        # Ativa as chaves estrangeiras
        cursor.execute('PRAGMA foreign_keys = ON;')
        # Criação da tabela 'categorias', se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único e autoincrementado
                nome TEXT NOT NULL UNIQUE              -- Nome da categoria, deve ser único
            )
        ''')
        # Criação da tabela 'livros', se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único e autoincrementado
                titulo TEXT NOT NULL UNIQUE,           -- Título do livro, deve ser único
                preco REAL NOT NULL,                   -- Preço do livro
                quantidade INTEGER NOT NULL,           -- Quantidade em estoque
                avaliacao INTEGER NOT NULL,            -- Avaliação do livro (1 a 5)
                categoria_id INTEGER,                  -- ID da categoria (chave estrangeira)
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)  -- Relacionamento com a tabela 'categorias'
            )
        ''')

def reorganizar_ids_categorias():
    """
    Reorganiza os IDs da tabela 'categorias' em ordem numérica e atualiza 
    os IDs correspondentes na tabela 'livros'.
    """
    with sqlite3.connect(DB_PATH) as conexao:
        cursor = conexao.cursor()
        # Desativa temporariamente as chaves estrangeiras
        cursor.execute('PRAGMA foreign_keys = OFF;')
        # Criação de uma tabela temporária para reorganizar os IDs
        cursor.execute('''
            CREATE TABLE categorias_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID novo e autoincrementado
                nome TEXT NOT NULL UNIQUE              -- Nome da categoria
            );
        ''')
        # Insere os dados da tabela original na tabela temporária, ordenados por nome
        cursor.execute('''
            INSERT INTO categorias_temp (nome)
            SELECT nome FROM categorias ORDER BY nome;
        ''')
        # Atualiza os IDs de 'categoria_id' na tabela 'livros' para corresponder aos novos IDs
        cursor.execute('''
            UPDATE livros
            SET categoria_id = (
                SELECT id FROM categorias_temp
                WHERE categorias_temp.nome = (
                    SELECT nome FROM categorias
                    WHERE categorias.id = livros.categoria_id
                )
            )
            WHERE categoria_id IS NOT NULL;
        ''')
        # Substitui a tabela original pela tabela temporária
        cursor.execute('DROP TABLE categorias;')
        cursor.execute('ALTER TABLE categorias_temp RENAME TO categorias;')
        # Reativa as chaves estrangeiras
        cursor.execute('PRAGMA foreign_keys = ON;')

def tratar_dados_livros(dados):
    """
    Realiza o tratamento e validação dos dados extraídos antes de inseri-los no banco.
    """
    dados_tratados = []
    for livro in dados:
        try:
            # Remove espaços e converte os dados para os tipos corretos
            livro_tratado = {
                'Título': livro['Título'].strip(),
                'Preço (£)': float(livro['Preço (£)']),
                'Quantidade': int(livro['Quantidade']),
                'Avaliação': int(livro['Avaliação']),
                'Categoria': livro['Categoria'].strip()
            }
            # Verifica se os dados são válidos
            if livro_tratado['Preço (£)'] > 0 and livro_tratado['Quantidade'] >= 0 and 1 <= livro_tratado['Avaliação'] <= 5:
                dados_tratados.append(livro_tratado)
            else:
                print(f"Dado inválido descartado: {livro}")
        except (ValueError, KeyError) as e:
            print(f"Erro ao tratar dados: {livro}. Erro: {e}")
    return dados_tratados

def inserir_dados_banco(dados):
    """
    Insere os dados extraídos e tratados no banco de dados.
    """
    with sqlite3.connect(DB_PATH) as conexao:
        cursor = conexao.cursor()
        for livro in dados:
            # Insere a categoria no banco, se ainda não existir
            cursor.execute('''
                INSERT OR IGNORE INTO categorias (nome)
                VALUES (?)
            ''', (livro['Categoria'],))
            # Obtém o ID da categoria inserida
            cursor.execute('SELECT id FROM categorias WHERE nome = ?', (livro['Categoria'],))
            categoria_id = cursor.fetchone()[0]
            # Insere o livro no banco, associado à categoria
            cursor.execute('''
                INSERT OR IGNORE INTO livros (titulo, preco, quantidade, avaliacao, categoria_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (livro['Título'], livro['Preço (£)'], livro['Quantidade'], livro['Avaliação'], categoria_id))
        conexao.commit()

def indicadores_performance():
    """
    Calcula e exibe indicadores de performance do catálogo.
    """
    with sqlite3.connect(DB_PATH) as conexao:
        cursor = conexao.cursor()
        # Calcula o total de livros bem avaliados (nota >= 4)
        cursor.execute('SELECT COUNT(*) FROM livros WHERE avaliacao >= 4')
        bem_avaliados = cursor.fetchone()[0]
        # Calcula o total de livros cadastrados
        cursor.execute('SELECT COUNT(*) FROM livros')
        total_livros = cursor.fetchone()[0]
        # Calcula o total de livros com estoque crítico (<= 5 unidades)
        cursor.execute('SELECT COUNT(*) FROM livros WHERE quantidade <= 5')
        estoque_critico = cursor.fetchone()[0]
        # Calcula o preço médio dos livros bem avaliados
        cursor.execute('SELECT AVG(preco) FROM livros WHERE avaliacao >= 4')
        preco_medio = cursor.fetchone()[0] or 0
    # Exibe os indicadores
    print("\nIndicadores de Performance:")
    print(f"Percentual Bem Avaliados (%): {round((bem_avaliados / total_livros * 100), 2) if total_livros else 0}")
    print(f"Percentual Estoque Crítico (%): {round((estoque_critico / total_livros * 100), 2) if total_livros else 0}")
    print(f"Preço Médio Bem Avaliados (£): {round(preco_medio, 2)}")

def visualizar_distribuicao_avaliacoes():
    """
    Gera gráficos de distribuição de avaliações.
    """
    with sqlite3.connect(DB_PATH) as conexao:
        cursor = conexao.cursor()
        # Obtém a contagem de avaliações agrupadas
        cursor.execute('SELECT avaliacao, COUNT(*) FROM livros GROUP BY avaliacao')
        distribuicao = dict(cursor.fetchall())

    sns.set(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Gráfico de barras para contagem de avaliações
    sns.barplot(
        x=list(distribuicao.keys()),
        y=list(distribuicao.values()),
        hue=list(distribuicao.keys()),  # Define o agrupamento de cores
        palette=sns.color_palette("muted", len(distribuicao)),
        legend=False,  # Remove a legenda, já que `hue` é redundante com `x`
        ax=axes[0]
    )
    axes[0].set_title("Distribuição de Avaliações (Contagem)")
    axes[0].set_xlabel("Avaliação (Estrelas)")
    axes[0].set_ylabel("Quantidade de Livros")

    # Gráfico de pizza para percentual de avaliações
    total = sum(distribuicao.values())
    percentual = [v / total * 100 for v in distribuicao.values()]
    axes[1].pie(
        percentual,
        labels=[f'{p} estrelas ({v:.1f}%)' for p, v in zip(distribuicao.keys(), percentual)],
        startangle=140,
        colors=sns.color_palette("pastel", len(distribuicao))
    )
    axes[1].set_title("Distribuição de Avaliações (Percentual)")

    plt.tight_layout()
    plt.show()

def extrair_dados_livros():
    """
    Extrai dados dos livros do site 'books.toscrape.com'.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)  # Abre o navegador visível
    context = browser.new_context()  # Cria um contexto de navegação
    page = context.new_page()  # Abre uma nova página no navegador

    print("\nIniciando extração de dados...")
    page.goto('https://books.toscrape.com/')
    page.wait_for_selector('.product_pod')  # Espera o carregamento dos elementos de livros

    dados = []
    # Extrai links para cada livro
    livros_links = page.eval_on_selector_all(
        '.product_pod h3 a',
        '(elements) => elements.map(element => ({ title: element.getAttribute("title"), href: element.href }))'
    )

    # Itera pelos links e coleta detalhes de cada livro
    for livro_info in livros_links:
        try:
            page.goto(livro_info['href'])
            page.wait_for_selector('.price_color')
            preco = float(page.query_selector('.price_color').inner_text().replace('£', ''))
            texto_estoque = page.query_selector('.instock').inner_text()
            quantidade = int(texto_estoque.replace('In stock (', '').replace(' available)', ''))
            estrelas = page.query_selector('p.star-rating').get_attribute('class').split()
            avaliacao = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}.get(next(filter(lambda x: x in ['One', 'Two', 'Three', 'Four', 'Five'], estrelas)), 0)
            categoria = page.query_selector('.breadcrumb li:nth-child(3) a').inner_text()

            dados.append({'Título': livro_info['title'], 'Preço (£)': preco, 'Quantidade': quantidade, 'Avaliação': avaliacao, 'Categoria': categoria})
        except Exception as e:
            print(f"Erro ao processar livro {livro_info['title']}: {e}")
            continue

    browser.close()
    playwright.stop()
    return dados

def main():
    """
    Função principal que orquestra a execução do programa.
    """
    criar_tabelas_banco()  # Cria as tabelas no banco de dados
    dados = tratar_dados_livros(extrair_dados_livros())  # Extrai e trata os dados dos livros
    inserir_dados_banco(dados)  # Insere os dados no banco
    reorganizar_ids_categorias()  # Reorganiza os IDs das categorias
    indicadores_performance()  # Calcula e exibe os indicadores de performance
    visualizar_distribuicao_avaliacoes()  # Gera gráficos de distribuição de avaliações

if __name__ == "__main__":
    main()