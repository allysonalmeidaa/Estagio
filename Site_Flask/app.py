from flask import Flask, render_template, abort
import sqlite3
import os

app = Flask(__name__)

# Define o caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Playwright_livros.db')

def conectar_banco():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

@app.route('/')
def index():
    """Rota para a página inicial"""
    try:
        conn = conectar_banco()
        if conn:
            cursor = conn.cursor()
            
            # Obtém estatísticas gerais
            cursor.execute('SELECT COUNT(*) as total_livros FROM livros')
            total_livros = cursor.fetchone()['total_livros']
            
            cursor.execute('SELECT COUNT(*) as total_categorias FROM categorias')
            total_categorias = cursor.fetchone()['total_categorias']
            
            conn.close()
            
            return render_template('index.html', 
                                total_livros=total_livros,
                                total_categorias=total_categorias)
    except Exception as e:
        print(f"Erro na rota index: {e}")
        abort(500)
    
    return render_template('index.html')

@app.route('/categorias')
def categorias():
    """Rota para a página de categorias"""
    try:
        conn = conectar_banco()
        if not conn:
            abort(500)
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.nome, c.contador_repeticoes,
                   COUNT(l.id) as total_livros
            FROM categorias c
            LEFT JOIN livros l ON c.id = l.categoria_id
            GROUP BY c.id, c.nome, c.contador_repeticoes
            ORDER BY c.nome ASC
        ''')
        categorias = cursor.fetchall()
        conn.close()
        
        return render_template('categorias.html', categorias=categorias)
    except Exception as e:
        print(f"Erro na rota categorias: {e}")
        abort(500)

@app.route('/livros')
def livros():
    """Rota para a página de todos os livros"""
    try:
        conn = conectar_banco()
        if not conn:
            abort(500)
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.titulo, l.preco, l.quantidade, l.avaliacao,
                   c.nome as categoria_nome
            FROM livros l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.titulo ASC
        ''')
        livros = cursor.fetchall()
        
        # Cálculo de estatísticas
        total_livros = len(livros)
        if total_livros > 0:
            preco_medio = sum(livro['preco'] for livro in livros) / total_livros
            categorias_unicas = len(set(livro['categoria_nome'] for livro in livros))
        else:
            preco_medio = 0
            categorias_unicas = 0
            
        conn.close()
        
        return render_template('livros.html', 
                             livros=livros,
                             total_livros=total_livros,
                             preco_medio=preco_medio,
                             categorias_unicas=categorias_unicas)
    except Exception as e:
        print(f"Erro na rota livros: {e}")
        abort(500)

@app.route('/livros/categoria/<int:categoria_id>')
def livros_por_categoria(categoria_id):
    """Rota para a página de livros de uma categoria específica"""
    try:
        conn = conectar_banco()
        if not conn:
            abort(500)
        
        cursor = conn.cursor()
        
        # Primeiro, verifica se a categoria existe
        cursor.execute('SELECT nome FROM categorias WHERE id = ?', (categoria_id,))
        categoria = cursor.fetchone()
        
        if not categoria:
            abort(404)  # Categoria não encontrada
            
        # Busca os livros da categoria
        cursor.execute('''
            SELECT l.titulo, l.preco, l.quantidade, l.avaliacao,
                   c.nome as categoria_nome
            FROM livros l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            WHERE l.categoria_id = ?
            ORDER BY l.titulo ASC
        ''', (categoria_id,))
        
        livros = cursor.fetchall()
        conn.close()
        
        return render_template('livros.html', 
                             livros=livros,
                             categoria_nome=categoria['nome'])
    except Exception as e:
        print(f"Erro na rota livros_por_categoria: {e}")
        abort(500)

@app.errorhandler(404)
def pagina_nao_encontrada(error):
    """Handler para erro 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def erro_servidor(error):
    """Handler para erro 500"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)