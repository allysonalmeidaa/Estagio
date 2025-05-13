from playwright.sync_api import sync_playwright
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, timeout=10)
        self.connection.execute('PRAGMA foreign_keys = ON;')

    def criar_tabelas(self):
        cursor = self.connection.cursor()
        try:
            # Cria a tabela de categorias com a nova coluna 'contador_repeticoes'
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                contador_repeticoes INTEGER NOT NULL DEFAULT 0
            );
            ''')
            # Cria a tabela de livros
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL UNIQUE,
                preco REAL NOT NULL,
                quantidade INTEGER NOT NULL,
                avaliacao INTEGER NOT NULL,
                categoria_id INTEGER,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            );
            ''')
        finally:
            cursor.close()

    def inserir_categoria(self, categoria_nome):
        cursor = self.connection.cursor()
        try:
            # Verifica se a categoria já existe
            cursor.execute('SELECT id FROM categorias WHERE nome = ?', (categoria_nome,))
            resultado = cursor.fetchone()

            if resultado:
                # Categoria já existe, retorna o ID
                categoria_id = resultado[0]
            else:
                # Insere uma nova categoria com contador inicializado em 0
                cursor.execute('''
                    INSERT INTO categorias (nome, contador_repeticoes)
                    VALUES (?, 0);
                ''', (categoria_nome,))
                categoria_id = cursor.lastrowid  # Recupera o ID da nova categoria

            self.connection.commit()
            return categoria_id
        finally:
            cursor.close()

    def inserir_livro(self, livro):
        cursor = self.connection.cursor()
        try:
            # Insere ou atualiza a categoria e recupera o ID
            categoria_id = self.inserir_categoria(livro['Categoria'])

            # Verifica se o livro já existe antes de inserir
            cursor.execute('SELECT COUNT(*) FROM livros WHERE titulo = ?', (livro['Título'],))
            livro_existe = cursor.fetchone()[0]

            if not livro_existe:
                # Insere o livro no banco de dados
                cursor.execute('''
                INSERT INTO livros (titulo, preco, quantidade, avaliacao, categoria_id)
                VALUES (?, ?, ?, ?, ?);
                ''', (livro['Título'], livro['Preço (£)'], livro['Quantidade'], livro['Avaliação'], categoria_id))

                # Incrementa o contador de repetições da categoria
                cursor.execute('''
                    UPDATE categorias
                    SET contador_repeticoes = contador_repeticoes + 1
                    WHERE id = ?;
                ''', (categoria_id,))

            self.connection.commit()
        finally:
            cursor.close()

    def reorganizar_ids_categorias(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute('PRAGMA foreign_keys = OFF;')  # Temporariamente desativa chaves estrangeiras
            # Cria uma tabela temporária para reorganizar os IDs com nomes em ordem alfabética
            cursor.execute('''
            CREATE TABLE categorias_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                contador_repeticoes INTEGER NOT NULL DEFAULT 0
            );
            ''')
            # Transfere os dados ordenados pelo nome para a tabela temporária
            cursor.execute('''
            INSERT INTO categorias_temp (nome, contador_repeticoes)
            SELECT nome, contador_repeticoes FROM categorias ORDER BY nome ASC;
            ''')
            # Atualiza as referências de IDs na tabela de livros
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
            cursor.execute('PRAGMA foreign_keys = ON;')  # Reativa chaves estrangeiras
            self.connection.commit()
        finally:
            cursor.close()

    def calcular_indicadores(self):
        """
        Calcula indicadores de performance do catálogo de livros.
        Retorna um dicionário com os resultados.
        """
        cursor = self.connection.cursor()
        try:
            # Quantidade de livros bem avaliados (4+ estrelas)
            cursor.execute('SELECT COUNT(*) FROM livros WHERE avaliacao >= 4')
            bem_avaliados = cursor.fetchone()[0]

            # Total de livros
            cursor.execute('SELECT COUNT(*) FROM livros')
            total_livros = cursor.fetchone()[0]

            # Calcula percentuais
            percentual_bem_avaliados = (bem_avaliados / total_livros * 100) if total_livros > 0 else 0
            cursor.execute('SELECT COUNT(*) FROM livros WHERE quantidade <= 5')
            estoque_critico = cursor.fetchone()[0]
            percentual_estoque_critico = (estoque_critico / total_livros * 100) if total_livros > 0 else 0

            # Preço médio de livros bem avaliados
            cursor.execute('SELECT AVG(preco) FROM livros WHERE avaliacao >= 4')
            preco_medio_bem_avaliados = cursor.fetchone()[0] or 0

            return {
                'Percentual Bem Avaliados (%)': round(percentual_bem_avaliados, 2),
                'Percentual Estoque Crítico (%)': round(percentual_estoque_critico, 2),
                'Preço Médio Bem Avaliados (£)': round(preco_medio_bem_avaliados, 2)
            }
        finally:
            cursor.close()

    def obter_distribuicao_avaliacoes(self):
        """
        Obtém a distribuição das avaliações dos livros.
        Retorna um dicionário com a contagem de cada avaliação.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute('SELECT avaliacao, COUNT(*) FROM livros GROUP BY avaliacao')
            distribuicao = dict(cursor.fetchall())
            return distribuicao
        finally:
            cursor.close()

    def close(self):
        self.connection.close()


# Classe responsável por fazer scraping no site
class BookScraper:
    def __init__(self, url):
        self.url = url  # URL do site alvo para scraping

    def extrair_dados(self):
        playwright = sync_playwright().start()  # Inicia o Playwright
        browser = playwright.chromium.launch(headless=False)  # Abre o navegador
        context = browser.new_context()
        page = context.new_page()

        page.goto(self.url)  # Acessa a URL
        page.wait_for_selector('.product_pod')  # Aguarda o carregamento dos livros

        livros_links = page.eval_on_selector_all(
            '.product_pod h3 a',
            '(elements) => elements.map(element => ({ title: element.getAttribute("title"), href: element.href }))'
        )

        dados = []
        for livro_info in livros_links:
            try:
                page.goto(livro_info['href'])
                page.wait_for_selector('.price_color')

                preco = float(page.query_selector('.price_color').inner_text().replace('£', ''))
                texto_estoque = page.query_selector('.instock').inner_text()
                quantidade = int(texto_estoque.replace('In stock (', '').replace(' available)', ''))

                estrelas_element = page.query_selector('p.star-rating')
                classes = estrelas_element.get_attribute('class')
                avaliacao = self._converter_avaliacao(classes)

                categoria = page.query_selector('.breadcrumb li:nth-child(3) a').inner_text()

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

    @staticmethod
    def _converter_avaliacao(classes):
        mapeamento_estrelas = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
        return next((mapeamento_estrelas[classe] for classe in classes.split() if classe in mapeamento_estrelas), 0)


class DataAnalyzer:
    def __init__(self, db_manager):
        self.db_manager = db_manager  # Conexão com o gerenciador de banco de dados

    def plotar_distribuicao_avaliacoes(self):
        distribuicao = self.db_manager.obter_distribuicao_avaliacoes()

        if not distribuicao:
            print("Erro: Não há dados suficientes para gerar os gráficos.")
            return

        sns.set(style="whitegrid")
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        sns.barplot(
            x=list(distribuicao.keys()),
            y=list(distribuicao.values()),
            hue=list(distribuicao.keys()),  # Corrige o FutureWarning
            palette=sns.color_palette("muted", len(distribuicao)),
            legend=False,
            ax=axes[0]
        )
        axes[0].set_title("Distribuição de Avaliações (Contagem)")
        axes[0].set_xlabel("Avaliação (Estrelas)")
        axes[0].set_ylabel("Quantidade de Livros")

        total = sum(distribuicao.values())
        percentual = [v / total * 100 for v in distribuicao.values()]
        axes[1].pie(
            percentual,
            labels=[f"{p} estrelas ({v:.1f}%)" for p, v in zip(distribuicao.keys(), percentual)],
            startangle=140,
            colors=sns.color_palette("pastel", len(distribuicao))
        )
        axes[1].set_title("Distribuição de Avaliações (Percentual)")

        plt.tight_layout()
        plt.show()


class Application:
    def __init__(self, db_path, scraper_url):
        self.db_manager = DatabaseManager(db_path)
        self.scraper = BookScraper(scraper_url)
        self.analyzer = DataAnalyzer(self.db_manager)

    def run(self):
        self.db_manager.criar_tabelas()  # Cria tabelas no banco
        dados = self.scraper.extrair_dados()  # Faz scraping dos dados

        for livro in dados:
            self.db_manager.inserir_livro(livro)  # Insere os dados no banco

        self.db_manager.reorganizar_ids_categorias()  # Reorganiza categorias

        indicadores = self.db_manager.calcular_indicadores()  # Calcula indicadores
        print("\nIndicadores de Performance:")
        for chave, valor in indicadores.items():
            print(f"{chave}: {valor}")

        self.analyzer.plotar_distribuicao_avaliacoes()  # Plota gráficos
        self.db_manager.close()  # Fecha conexão com o banco


if __name__ == "__main__":
    app = Application(
        db_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Playwright_livros.db'),
        scraper_url='https://books.toscrape.com/'
    )
    app.run()