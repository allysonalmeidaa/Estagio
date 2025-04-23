import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os

# Configuração do WebDriver
service = Service()  
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Acessa o site
url = 'https://books.toscrape.com/'
driver.get(url)

# Coleta os links
links = driver.find_elements(By.TAG_NAME, 'a')
if len(links) > 54:
    Titleelements = links[54:94:2]
else:
    print("Não há links suficientes na página.")
    Titleelements = []

# Coleta os títulos
titlelist = [title.get_attribute('title') for title in Titleelements]

# Coleta as quantidades em estoque
estoquelista = []
for title in Titleelements:
    try:
        title.click()
        qtdestoque = int(driver.find_element(By.CLASS_NAME, 'instock').text.replace('In stock (' , '').replace(' available)', ''))
        estoquelista.append(qtdestoque)
        driver.back()
    except Exception as e:
        print(f"Erro ao processar o título: {e}")
        estoquelista.append(0)

# Cria um DataFrame com os dados
df = pd.DataFrame({
    'Nome do Livro': titlelist,
    'Quantidade em Estoque': estoquelista
})

# Obtém o diretório atual do script e cria o caminho do arquivo
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_excel = os.path.join(diretorio_atual, 'livros_estoque.xlsx')

# Exporta o DataFrame para um arquivo Excel
df.to_excel(caminho_excel, index=False)

print(f"Arquivo Excel criado com sucesso em: {caminho_excel}")

# Fecha o navegador
driver.quit()