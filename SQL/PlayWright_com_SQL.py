# Importação das bibliotecas necessárias
from playwright.sync_api import sync_playwright  # Para automação web e scraping
import sqlite3  # Para gerenciamento do banco de dados SQLite
import os  # Para operações com arquivos e diretórios
import matplotlib.pyplot as plt  # Para criação de gráficos
import seaborn as sns  # Para visualização de dados estatísticos

def criar_tabelas_banco(conexao):
    """
    Cria as tabelas 'livros' e 'categorias' no banco de dados SQLite.
    Parâmetros:
        conexao: Conexão com o banco de dados SQLite
    """
    cursor = conexao.cursor()
    cursor.execute('PRAGMA foreign_keys = ON;')  # Ativa o suporte a chaves estrangeiras

    try:
        # Cria a tabela de categorias com ID autoincremental e nome único
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
        ''')

        # Cria a tabela de livros com relação à tabela de categorias
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL UNIQUE,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            avaliacao INTEGER NOT NULL,
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
        ''')
    except sqlite3.OperationalError as e:
        print(f"Erro ao criar tabelas: {e}")
    finally:
        cursor.close()

def tratar_dados_livros(dados):
    """
    Realiza validação e limpeza dos dados dos livros antes da inserção no banco.
    Parâmetros:
        dados: Lista de dicionários contendo informações dos livros
    Retorna:
        Lista de dicionários com dados tratados
    """
    dados_tratados = []
    for livro in dados:
        try:
            # Extrai e trata cada campo do livro
            titulo = livro['Título'].strip() if 'Título' in livro else None
            preco = float(livro['Preço (£)']) if 'Preço (£)' in livro else 0.0
            quantidade = int(livro['Quantidade']) if 'Quantidade' in livro else 0
            avaliacao = int(livro['Avaliação']) if 'Avaliação' in livro else 0
            categoria = livro['Categoria'].strip() if 'Categoria' in livro else "Sem Categoria"

            # Valida os campos obrigatórios
            if not titulo or preco <= 0 or quantidade < 0 or avaliacao not in range(1, 6):
                print(f"Dados inválidos encontrados e descartados: {livro}")
                continue

            dados_tratados.append({
                'Título': titulo,
                'Preço (£)': preco,
                'Quantidade': quantidade,
                'Avaliação': avaliacao,
                'Categoria': categoria,
            })
        except Exception as e:
            print(f"Erro ao tratar dados do livro: {livro}. Erro: {e}")
            continue

    return dados_tratados

def inserir_categoria(cursor, categoria_nome):
    """
    Insere uma nova categoria no banco de dados se ela não existir.
    Parâmetros:
        cursor: Cursor do banco de dados
        categoria_nome: Nome da categoria a ser inserida
    Retorna:
        ID da categoria inserida ou existente
    """
    try:
        # Tenta inserir a categoria se ela não existir
        cursor.execute('''
        INSERT OR IGNORE INTO categorias (nome)
        VALUES (?)
        ''', (categoria_nome,))

        # Recupera o ID da categoria
        cursor.execute('SELECT id FROM categorias WHERE nome = ?', (categoria_nome,))
        categoria_id = cursor.fetchone()
        return categoria_id[0] if categoria_id else None
    except sqlite3.OperationalError as e:
        print(f"Erro ao inserir categoria '{categoria_nome}': {e}")
        return None

def inserir_dados_banco(conexao, dados):
    """
    Insere os dados dos livros no banco de dados.
    Parâmetros:
        conexao: Conexão com o banco de dados
        dados: Lista de dicionários com informações dos livros
    """
    cursor = conexao.cursor()

    try:
        for livro in dados:
            # Insere a categoria e obtém seu ID
            categoria_id = inserir_categoria(cursor, livro['Categoria'])
            if categoria_id is None:
                print(f"Erro: Categoria '{livro['Categoria']}' não pôde ser inserida ou encontrada.")
                continue

            # Insere o livro com referência à categoria
            cursor.execute('''
            INSERT OR IGNORE INTO livros (titulo, preco, quantidade, avaliacao, categoria_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (livro['Título'], livro['Preço (£)'], livro['Quantidade'], livro['Avaliação'], categoria_id))

        conexao.commit()
    except sqlite3.OperationalError as e:
        print(f"Erro ao inserir dados no banco: {e}")
    finally:
        cursor.close()

def reorganizar_ids_categorias(conexao):
    """
    Reorganiza os IDs das categorias em ordem numérica sequencial.
    Parâmetros:
        conexao: Conexão com o banco de dados
    """
    cursor = conexao.cursor()
    try:
        # Desativa temporariamente as chaves estrangeiras
        cursor.execute('PRAGMA foreign_keys = OFF;')

        # Cria uma tabela temporária para reorganização
        cursor.execute('''
        CREATE TABLE categorias_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        );
        ''')

        # Transfere dados ordenados para a tabela temporária
        cursor.execute('''
        INSERT INTO categorias_temp (nome)
        SELECT nome FROM categorias ORDER BY nome;
        ''')

        # Atualiza as referências na tabela de livros
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

        # Substitui a tabela original
        cursor.execute('DROP TABLE categorias;')
        cursor.execute('ALTER TABLE categorias_temp RENAME TO categorias;')

        cursor.execute('PRAGMA foreign_keys = ON;')
        conexao.commit()
        print("IDs das categorias reorganizados com sucesso.")
    except sqlite3.OperationalError as e:
        print(f"Erro ao reorganizar IDs das categorias: {e}")
    finally:
        cursor.close()

def indicadores_performance(db_path):
    """
    Calcula métricas de performance do catálogo de livros.
    Parâmetros:
        db_path: Caminho para o arquivo do banco de dados
    Retorna:
        Dicionário com indicadores calculados
    """
    conexao = sqlite3.connect(db_path)
    cursor = conexao.cursor()

    # Calcula quantidade de livros bem avaliados (4+ estrelas)
    cursor.execute('SELECT COUNT(*) FROM livros WHERE avaliacao >= 4')
    bem_avaliados = cursor.fetchone()[0]

    # Calcula total de livros
    cursor.execute('SELECT COUNT(*) FROM livros')
    total_livros = cursor.fetchone()[0]

    # Calcula percentual de livros bem avaliados
    percentual_bem_avaliados = (bem_avaliados / total_livros * 100) if total_livros > 0 else 0

    # Calcula quantidade de livros com estoque crítico (≤ 5 unidades)
    cursor.execute('SELECT COUNT(*) FROM livros WHERE quantidade <= 5')
    estoque_critico = cursor.fetchone()[0]

    # Calcula percentual de livros em estoque crítico
    percentual_estoque_critico = (estoque_critico / total_livros * 100) if total_livros > 0 else 0

    # Calcula preço médio dos livros bem avaliados
    cursor.execute('SELECT AVG(preco) FROM livros WHERE avaliacao >= 4')
    preco_medio_bem_avaliados = cursor.fetchone()[0] or 0

    conexao.close()

    return {
        'Percentual Bem Avaliados (%)': round(percentual_bem_avaliados, 2),
        'Percentual Estoque Crítico (%)': round(percentual_estoque_critico, 2),
        'Preço Médio Bem Avaliados (£)': round(preco_medio_bem_avaliados, 2)
    }

def visualizar_distribuicao_avaliacoes(db_path):
    """
    Gera gráficos para visualizar a distribuição das avaliações dos livros.
    Parâmetros:
        db_path: Caminho para o arquivo do banco de dados
    """
    conexao = sqlite3.connect(db_path)
    cursor = conexao.cursor()

    # Obtém a distribuição das avaliações
    cursor.execute('SELECT avaliacao, COUNT(*) FROM livros GROUP BY avaliacao')
    distribuicao = dict(cursor.fetchall())

    conexao.close()

    if not distribuicao:
        print("Erro: Não há dados suficientes para gerar os gráficos.")
        return

    # Configura o estilo dos gráficos
    sns.set(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Cria gráfico de barras
    sns.barplot(
        x=list(distribuicao.keys()),
        y=list(distribuicao.values()),
        hue=list(distribuicao.keys()),
        palette=sns.color_palette("muted", len(distribuicao)),
        legend=False,
        ax=axes[0]
    )
    axes[0].set_title("Distribuição de Avaliações (Contagem)")
    axes[0].set_xlabel("Avaliação (Estrelas)")
    axes[0].set_ylabel("Quantidade de Livros")

    # Cria gráfico de pizza
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
    Realiza web scraping do site books.toscrape.com para extrair dados dos livros.
    Retorna:
        Lista de dicionários com informações dos livros
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("\nIniciando extração de dados...")

    # Acessa a página inicial
    page.goto('https://books.toscrape.com/')
    page.wait_for_selector('.product_pod')

    dados = []

    # Obtém links dos livros
    livros_links = page.eval_on_selector_all(
        '.product_pod h3 a',
        '(elements) => elements.map(element => ({ title: element.getAttribute("title"), href: element.href }))'
    )

    # Processa cada livro
    for livro_info in livros_links:
        try:
            page.goto(livro_info['href'])
            page.wait_for_selector('.price_color')
            page.wait_for_selector('.breadcrumb li:nth-child(3) a')

            # Extrai informações do livro
            preco = float(page.query_selector('.price_color').inner_text().replace('£', ''))
            texto_estoque = page.query_selector('.instock').inner_text()
            quantidade = int(texto_estoque.replace('In stock (', '').replace(' available)', ''))

            # Converte avaliação em estrelas para número
            estrelas_element = page.query_selector('p.star-rating')
            classes = estrelas_element.get_attribute('class')
            mapeamento_estrelas = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
            avaliacao = next((mapeamento_estrelas[classe] for classe in classes.split() if classe in mapeamento_estrelas), 0)

            categoria = page.query_selector('.breadcrumb li:nth-child(3) a').inner_text()

            # Adiciona dados do livro à lista
            dados.append({
                'Título': livro_info['title'],
                'Preço (£)': preco,
                'Quantidade': quantidade,
                'Avaliação': avaliacao,
                'Categoria': categoria,
            })
        except Exception as e:
            print(f"Erro ao processar livro {livro_info['title']}: {str(e)}")
            continue

    browser.close()
    playwright.stop()
    return dados

def main():
    """
    Função principal que coordena o fluxo do programa.
    """
    # Define o caminho do banco de dados
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Playwright_livros.db')

    # Estabelece conexão com o banco de dados
    conexao = sqlite3.connect(db_path, timeout=10)
    criar_tabelas_banco(conexao)

    # Extrai e processa os dados
    dados = extrair_dados_livros()
    dados_tratados = tratar_dados_livros(dados)
    inserir_dados_banco(conexao, dados_tratados)

    # Reorganiza as categorias
    reorganizar_ids_categorias(conexao)

    # Gera e exibe indicadores
    indicadores = indicadores_performance(db_path)
    print("\nIndicadores de Performance:")
    for chave, valor in indicadores.items():
        print(f"{chave}: {valor}")

    # Gera visualizações
    visualizar_distribuicao_avaliacoes(db_path)
    conexao.close()

# Ponto de entrada do programa
if __name__ == "__main__":
    main()