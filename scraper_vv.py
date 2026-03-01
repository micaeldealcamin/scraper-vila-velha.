import requests
from bs4 import BeautifulSoup
import pandas as pd
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import time

# Configurações do Portal
BASE_URL = "https://www.vilavelha.es.gov.br"
LISTA_URL = f"{BASE_URL}/noticias"

# Headers para simular um navegador Chrome real e evitar bloqueios
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}

def extrair_noticias():
    print(f"🚀 Conectando ao portal de Vila Velha...")
    session = requests.Session()
    
    try:
        # Usando a sua internet local, o timeout dificilmente ocorrerá
        response = session.get(LISTA_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    # Localizador CSS específico que você identificou
    cards = soup.find_all('div', class_='col-xs-12 col-sm-6 col-lg-4 px-lg-5')
    
    dados_finais = []
    print(f"✅ {len(cards)} notícias encontradas. Extraindo detalhes...")

    for card in cards[:12]: # Processa as 12 mais recentes
        try:
            link_rel = card.find('a')['href']
            url_noticia = f"{BASE_URL}{link_rel}"
            
            # Entra na página interna da notícia
            res_int = session.get(url_noticia, headers=HEADERS, timeout=15)
            soup_int = BeautifulSoup(res_int.text, 'html.parser')
            area = soup_int.find('div', class_='area-noticia')
            
            if area:
                titulo = area.find('h1', class_='title').get_text(strip=True)
                
                # Data de publicação
                info_criacao = area.find('div', class_='created')
                data_str = info_criacao.get_text(strip=True).replace('Publicado em:', '').strip() if info_criacao else "Sem data"
                
                # Foto principal
                img_tag = area.find('img', class_='img-responsive')
                foto_url = img_tag['src'] if img_tag else ""
                if foto_url.startswith('/'): foto_url = f"{BASE_URL}{foto_url}"
                
                # Conteúdo da notícia
                desc_tag = area.find('p', class_='description')
                conteudo = desc_tag.get_text(separator='\n', strip=True) if desc_tag else ""

                dados_finais.append({
                    'titulo': titulo,
                    'data': data_str,
                    'link': url_noticia,
                    'foto': foto_url,
                    'conteudo': conteudo
                })
                print(f"✔️ {titulo[:50]}...")
            
            time.sleep(1) # Pausa amigável
        except Exception as e:
            continue

    return dados_finais

def gerar_arquivos(lista):
    if not lista: return

    # Salva Planilha
    pd.DataFrame(lista).to_csv('noticias_vv.csv', index=False, encoding='utf-8-sig')
    print("\n📊 Planilha 'noticias_vv.csv' criada.")

    # Gerar RSS (Formato XML para leitores de feed)
    fg = FeedGenerator()
    fg.id(LISTA_URL)
    fg.title('Notícias Vila Velha')
    fg.link(href=BASE_URL, rel='alternate')
    fg.description('Feed extraído automaticamente via Python')
    
    for item in lista:
        fe = fg.add_entry()
        fe.id(item['link'])
        fe.title(item['titulo'])
        fe.link(href=item['link'])
        # Formata o RSS com imagem para o leitor (ex: Feedly)
        html_rss = f"<img src='{item['foto']}' style='width:100%'><br><p>{item['conteudo'][:600]}...</p>"
        fe.description(html_rss)
        fe.pubDate(datetime.now(pytz.timezone('America/Sao_Paulo')))

    fg.rss_file('feed_vila_velha_vv.xml')
    print("📡 Feed RSS 'feed_vila_velha_vv.xml' gerado com sucesso!")

if __name__ == "__main__":
    noticias = extrair_noticias()
    gerar_arquivos(noticias)
