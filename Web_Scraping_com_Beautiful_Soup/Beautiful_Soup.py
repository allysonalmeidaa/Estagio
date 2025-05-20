from bs4 import BeautifulSoup
import requests
import pandas as pd
import os 

# Configuração do User-Agent
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
headers = {'User-Agent': user_agent}

# URL da página
url = 'https://minecraft.fandom.com/wiki/Tutorials/Best_enchantments_guide'

# Faz a requisição HTTP
page = requests.get(url, headers=headers)

# Verifica o status da requisição
if page.status_code == 200:
    print(f"Status da requisição: {page.status_code} (Sucesso)\n")
else:
    print(f"Erro na requisição: {page.status_code}")
    exit()

# Obtém o conteúdo HTML da página
html = page.text

# Faz o parsing do HTML com BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Encontra todos os elementos <span> com a classe 'sprite-text'
elements = soup.find_all('span', attrs={'class': 'sprite-text'})

# Extrai o texto de cada elemento encontrado
objects = [element.get_text(strip=True) for element in elements]

# Exibe os objetos encontrados
print("Objetos encontrados:")
for obj in objects:
    print(f"- {obj}")

# Obtém o diretório do script atual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Cria o caminho completo para o arquivo Excel
excel_path = os.path.join(current_dir, "objetos_encontrados.xlsx")

# Exporta os objetos para um arquivo Excel
df = pd.DataFrame(objects, columns=["Objetos"])
df.to_excel(excel_path, index=False)

print(f"\nOs objetos foram exportados para '{excel_path}'.")