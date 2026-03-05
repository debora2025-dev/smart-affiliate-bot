import sys
import os
import re
import time
import random
import io
import requests
import pyperclip
import pandas as pd
import urllib.parse
from datetime import datetime
from PIL import Image
from io import BytesIO
import win32clipboard
import json

# Imports do Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- CONFIGURAÇÕES DE ENGENHARIA DE CHATBOT ---
SIMULAR_DIGITACAO = True
DELAY_MIN_ENTRE_MENSAGENS = 5
DELAY_MAX_ENTRE_MENSAGENS = 15

# --- FUNÇÕES DE UTILIDADE ---

def human_delay(min_s=1, max_s=3):
    """Gera uma pausa aleatória com jitter para simular comportamento humano."""
    tempo = random.uniform(min_s, max_s)
    time.sleep(tempo)

def formatar_para_whatsapp(texto_html):
    """
    Converte tags HTML/Telegram para Markdown do WhatsApp e limpa a mensagem.
    Foca em escaneabilidade e Link Preview.
    """
    if not texto_html: return ""
    
    # Conversões básicas de estilo
    mapa_tags = {
        "<b>": "*", "</b>": "*",
        "<strong>": "*", "</strong>": "*",
        "<i>": "_", "</i>": "_",
        "<em>": "_", "</em>": "_",
        "<s>": "~", "</s>": "~",
        "<strike>": "~", "</strike>": "~"
    }
    
    texto_whats = texto_html
    for tag, replacement in mapa_tags.items():
        texto_whats = texto_whats.replace(tag, replacement)
        
    # Remove tags de link do Telegram (mantendo o link seco para o preview do WhatsApp)
    # Ex: <a href='URL'>TEXTO</a> -> URL
    texto_whats = re.sub(r'<a href=[\'"](.*?)[\'"]>(.*?)</a>', r'\1', texto_whats)
    
    # Garante que emojis tenham espaço ao redor se necessário (opcional)
    # Adiciona uma quebra de linha extra antes do link final se houver um link no texto
    if "http" in texto_whats:
        partes = texto_whats.split("http")
        if len(partes) > 1:
            link = "http" + partes[-1]
            corpo = "http".join(partes[:-1]).strip()
            texto_whats = f"{corpo}\n\n{link}"
            
    return texto_whats.strip()

def simular_digitacao(driver, elemento, texto):
    """Simula a digitação de uma mensagem para enganar sistemas de detecção de bot."""
    if not SIMULAR_DIGITACAO:
        elemento.send_keys(texto)
        return

    # No WhatsApp Web, colar o texto inteiro é comum em humanos (copy-paste), 
    # mas o ato de clicar e esperar um pouco antes de colar ajuda muito.
    human_delay(0.5, 1.5)
    
    # Para mensagens muito curtas, digitamos letra a letra
    if len(texto) < 20:
        for char in texto:
            elemento.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
    else:
        # Para mensagens longas (ofertas), simulamos o "pensar" e o "colar"
        pyperclip.copy(texto)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        human_delay(1, 2)

def validar_link_afiliado(url, loja):
    """Verifica se o link contém os IDs de rastreio necessários."""
    if not url: return False
    
    regras = {
        "AMAZON": ["tag=celle-20"],
        "MAGALU": ["magazinevoce.com.br/magazinecelle"],
        "SHOPEE": ["shope.ee", "shopee.com.br/universal-link"],
        "MERCADOLIVRE": ["mercadolivre.com.br/social"]
    }
    
    for tag in regras.get(loja, []):
        if tag in url:
            return True
    return True

def baixar_imagem_temporaria(url_imagem, nome_arquivo="temp_oferta.jpg"):
    """Baixa a imagem da oferta para o PC para poder ser copiada."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url_imagem, headers=headers, timeout=10)
        if resposta.status_code == 200:
            with open(nome_arquivo, 'wb') as f:
                f.write(resposta.content)
            return os.path.abspath(nome_arquivo)
    except Exception as e:
        print(f"| ❌ Erro ao baixar imagem: {e}")
    return None

def copiar_imagem_para_clipboard(caminho_imagem):
    """Mágica que coloca a imagem na área de transferência do Windows."""
    image = Image.open(caminho_imagem)
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def produto_eh_bloqueado(titulo):
    """Verifica se o título contém algum termo da lista de bloqueio."""
    if not titulo: return False
    titulo_lower = titulo.lower()
    for termo in TERMOS_BLOQUEADOS:
        if termo.lower() in titulo_lower:
            return True
    return False

def extrair_valor_numerico(preco_texto):
    if not preco_texto:
        return None
    try:
        # Encontra todos os padrões de preço (0,00 ou 0.00)
        # Primeiro, removemos pontos de milhar para não confundir (ex: 1.234,56 -> 1234,56)
        txt = preco_texto.replace('.', '')
        # Agora buscamos números com vírgula (formato BR)
        matches = re.findall(r'\d+,\d+', txt)
        
        precos = []
        for m in matches:
            val = float(m.replace(',', '.'))
            precos.append(val)
        
        if precos:
            # Em caso de range (R$ 10 - R$ 20), pegamos o MENOR preço
            return min(precos)
            
        # Fallback para números sem vírgula
        match_simples = re.findall(r'\d+\.?\d*', preco_texto.replace(',', '.'))
        if match_simples:
            return float(match_simples[0])
            
        return None
    except Exception:
        return None
    
def formatar_preco_br(preco):
    try:
        preco = float(preco)
    except (ValueError, TypeError):
        return str(preco)
    parte_inteira = int(preco)
    parte_decimal = int(round((preco - parte_inteira) * 100))
    texto_inteiro = "{:,}".format(parte_inteira).replace(",", ".")
    texto_decimal = f"{parte_decimal:02d}"
    return f"R$ {texto_inteiro},{texto_decimal}"

def gerar_link_afiliado(url_original, loja):
    try:
        if loja == "MAGALU":
            if "magazinevoce.com.br/magazinecelle" not in url_original:
                codigo_produto = url_original.split('/')[-2] 
                return f"https://www.magazinevoce.com.br/magazinecelle/p/{codigo_produto}/"
            return url_original
            
        elif loja == "AMAZON":
            parsed = urllib.parse.urlparse(url_original)
            query = urllib.parse.parse_qs(parsed.query)
            query['tag'] = ['celle-20'] 
            new_query = urllib.parse.urlencode(query, doseq=True)
            return parsed._replace(query=new_query).geturl()
            
        elif loja == "SHOPEE":
            return url_original
            
    except Exception as e:
        print(f"Erro ao gerar link afiliado: {e}")
        return url_original

def gerar_link_ml_via_barra_topo(driver):
    print("| 🔗 ML: Buscando barra de afiliado no topo...")
    
    try:
        try:
            botao_share = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='generate_link_button']"))
            )
            botao_share.click()
        except:
            botao_share = driver.find_element(By.XPATH, "//button[contains(., 'Compartilhar')]")
            driver.execute_script("arguments[0].click();", botao_share)

        print("| Aguardando modal...")

        try:
            pyperclip.copy("")
            
            botao_copiar = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='copy-button__label_link']"))
            )
            
            driver.execute_script("arguments[0].click();", botao_copiar)
            print("| ✅ Cliquei no botão de copiar (via ID exato)!")
            
            time.sleep(1.0)
            link_final = pyperclip.paste()
            
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            
            if "mercadolivre" in link_final or "ml.com" in link_final:
                print(f"| 🎯 SUCESSO! Link capturado: {link_final}")
                return link_final

        except Exception as e:
            print(f"| ⚠️ Falha ao clicar no botão de cópia: {e}")
            
            try:
                print("| Tentando ler direto da caixa de texto...")
                caixa_texto = driver.find_element(By.CSS_SELECTOR, "textarea[data-testid='text-field__label_link']")
                link_direto = caixa_texto.get_attribute("value")
                
                if link_direto and "http" in link_direto:
                    print(f"| 🎯 SUCESSO (PLANO B)! Link lido: {link_direto}")
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    return link_direto
            except: pass

    except Exception as e:
        print(f"| ❌ Erro geral na barra: {e}")
        try: ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except: pass
        
    return None

def extrair_dados_produto_ml(driver):
    try:
        titulo = driver.find_element(By.CSS_SELECTOR, "h1.ui-pdp-title").text.strip()
    except:
        titulo = "Produto Mercado Livre"

    preco_atual = None
    preco_antigo = None
    
    try:
        container_preco = driver.find_element(By.CSS_SELECTOR, ".ui-pdp-price__second-line")
        elem_atual = container_preco.find_element(By.CSS_SELECTOR, ".andes-money-amount__fraction")
        preco_atual = float(elem_atual.text.replace(".", "").replace(",", "."))
    except: pass

    try:
        elem_antigo = driver.find_element(By.CSS_SELECTOR, ".ui-pdp-price__original-value .andes-money-amount__fraction")
        preco_antigo = float(elem_antigo.text.replace(".", "").replace(",", "."))
    except: pass

    nota = 0.0
    try:
        elem_nota = driver.find_element(By.CSS_SELECTOR, ".ui-pdp-reviews__rating")
        nota = float(elem_nota.text.strip())
    except:
        try:
            header = driver.find_element(By.CSS_SELECTOR, ".ui-pdp-header__info")
            texto_header = header.text
            match = re.search(r"(\d\.\d)", texto_header)
            if match:
                nota = float(match.group(1))
        except: pass

    image_url = None
    try:
        img = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "figure.ui-pdp-gallery__figure img"))
        )
        image_url = img.get_attribute("src")
    except:
        try:
            img = driver.find_element(By.CSS_SELECTOR, "img.ui-pdp-image")
            image_url = img.get_attribute("src")
        except: pass

    # --- NOVO: Extração de Popularidade (Mais Vendidos) ---
    vendas_count = 0
    is_best_seller = False
    try:
        # Checa selo "1º mais vendido"
        best_seller_elem = driver.find_elements(By.CSS_SELECTOR, ".ui-pdp-promotions-pill-label__container")
        for b in best_seller_elem:
            if "mais vendido" in b.text.lower():
                is_best_seller = True
                break
        
        # Checa quantidade de vendidos (ex: "5.000+ vendidos")
        header_info = driver.find_element(By.CSS_SELECTOR, ".ui-pdp-header__subtitle").text.lower()
        match_vendas = re.search(r"(\d+[\d\.]*)\+?\s*vendidos", header_info)
        if match_vendas:
            vendas_str = match_vendas.group(1).replace(".", "")
            vendas_count = int(vendas_str)
    except: pass

    return titulo, preco_atual, preco_antigo, nota, image_url, vendas_count, is_best_seller

# =========================================================
# PARTE SHOPEE (CORRIGIDA)
# =========================================================
def focar_aba_whatsapp(driver):
    """Procura e foca na aba que contém o WhatsApp Web."""
    print("| 🔍 Procurando aba do WhatsApp...")
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "WhatsApp" in driver.title or "web.whatsapp.com" in driver.current_url:
            print("| ✅ Aba do WhatsApp encontrada e focada.")
            return True
    print("| ❌ WhatsApp não encontrado nas abas abertas!")
    return False

def processar_painel_shopee(driver, produtos_processados_set):
    print("\n======== 🟠 SHOPEE (PAINEL -> NOVA ABA SEGURA) ========")
    url_painel = "https://affiliate.shopee.com.br/offer/product_offer"
    
    if url_painel not in driver.current_url:
        driver.get(url_painel)
    
    print("\n" + "="*50)
    print("🚨 INSTRUÇÃO: NÃO MEXA NO MOUSE 🚨")
    print("O robô vai calcular matematicamente qual é a nova aba.")
    print("="*50)
    
    print("🚨 INSTRUÇÃO: Aguardando carregamento da lista (Max 60s)...")
    print("="*50)
    
    # input("👉 APERTE [ENTER] AQUI QUANDO A LISTA APARECER...") # REMOVIDO PARA AUTOMATIZAÇÃO

    try:
        wait = WebDriverWait(driver, 60) # Timeout aumentado para dar tempo de resolver captcha se aparecer
        aba_painel = driver.current_window_handle 

        # Espera até que um botão 'Obter link' esteja visível, indicando que a lista carregou
        print("| ⏳ Aguardando lista de ofertas...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Obter link')]")))
        print("| ✅ Lista carregada! Prosseguindo...")

        # 1. ROLAGEM
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)

        print("| 🕵️ Mapeando produtos no painel...")
        botoes_painel = driver.find_elements(By.XPATH, "//*[contains(text(), 'Obter link')]")
        produtos_encontrados = [b for b in botoes_painel if b.is_displayed()]
        print(f"| ✅ Produtos listados: {len(produtos_encontrados)}")

        contador_envios = 0
        MAX_SHOPEE = 3

        for i in range(len(produtos_encontrados)):
            if contador_envios >= MAX_SHOPEE: break
            
            # Garante foco no Painel
            if driver.current_window_handle != aba_painel:
                driver.switch_to.window(aba_painel)
            
            # Recarrega lista
            botoes_painel = driver.find_elements(By.XPATH, "//*[contains(text(), 'Obter link')]")
            produtos_encontrados = [b for b in botoes_painel if b.is_displayed()]
            
            if i >= len(produtos_encontrados): break
            botao_ref = produtos_encontrados[i]

            try:
                # --- BUSCA ROBUSTA PELO CARD DO PRODUTO ---
                # Em vez de fixar o número de ../, subimos até encontrar um elemento que pareça um card ou linha
                card_painel = None
                try:
                    # Tenta encontrar o container que engloba o botão e a imagem/título
                    # Geralmente na Shopee é uma div com uma classe específica de item ou estrutura de tabela
                    card_painel = botao_ref.find_element(By.XPATH, "./ancestor::div[contains(@class, 'offer-card') or contains(@class, 'product-item') or contains(@style, 'margin')]")
                except:
                    # Fallback: sobe 5 níveis se a busca por classe falhar
                    card_painel = botao_ref.find_element(By.XPATH, "./../../../../..")
                
                titulo_previo = "Produto Shopee"
                try:
                    titulo_previo = card_painel.text.split('\n')[0]
                except: pass

                if titulo_previo in produtos_processados_set: continue

                if produto_eh_bloqueado(titulo_previo):
                    print(f"| 🚫 BLOQUEADO: '{titulo_previo}' contém termo proibido.")
                    produtos_processados_set.add(titulo_previo)
                    continue

                print(f"| 👆 Tentando abrir produto: {titulo_previo[:30]}...")

                # ============================================================
                # 🧠 LÓGICA DE OURO: SNAPSHOT DAS ABAS
                # ============================================================
                abas_antes = set(driver.window_handles) 

                # ROLAGEM E CLIQUE
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", card_painel)
                time.sleep(1.5)

                try:
                    # Tenta clicar na imagem ou no título, que são links mais diretos
                    link_clicavel = card_painel.find_element(By.TAG_NAME, "img")
                    print("| -> Clicando na IMAGEM...")
                    driver.execute_script("arguments[0].click();", link_clicavel)
                except:
                    print("| -> Clicando no CARD inteiro...")
                    driver.execute_script("arguments[0].click();", card_painel)

                print("| ⏳ Aguardando nova aba (5s)...")
                time.sleep(5) 
                
                abas_depois = set(driver.window_handles)
                nova_aba_conjunto = abas_depois - abas_antes
                
                if not nova_aba_conjunto:
                    print("| ⚠️ Nenhuma aba nova detectada. Tentando CLIQUE ALTERNATIVO (ActionChains)...")
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(driver).move_to_element(card_painel).click().perform()
                    time.sleep(5)
                    abas_depois = set(driver.window_handles)
                    nova_aba_conjunto = abas_depois - abas_antes

                if not nova_aba_conjunto:
                    print("| ❌ FALHA: O clique nao abriu uma nova aba.")
                    continue
                
                aba_produto = list(nova_aba_conjunto)[0]
                driver.switch_to.window(aba_produto)
                
                # ============================================================
                # NA NOVA ABA (SEGURA)
                # ============================================================
                
                # Tenta extrair dados com seletores mais robustos
                titulo = None
                preco = 0.0
                preco_antigo = None
                
                try:
                    # PREÇO ATUAL (NOVOS SELETORES)
                    seletores_atual = [".IZPeQz.B67UQ0", ".pqTWkA", ".shopee-product-info__header__real-price"]
                    for sel in seletores_atual:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, sel)
                            valor = extrair_valor_numerico(elem.text)
                            if valor and valor > 0:
                                preco = valor
                                break
                        except: continue
                    
                    # PREÇO ANTIGO
                    seletores_antigo = [".ZA5sW5", ".v67p8K", ".shopee-product-info__header__price-before"]
                    for sel in seletores_antigo:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, sel)
                            valor = extrair_valor_numerico(elem.text)
                            if valor and valor > 0:
                                preco_antigo = valor
                                break
                        except: continue
                except: pass

                # VENDAS E NOTA (NOVOS SELETORES)
                vendas_count = 0
                nota = 0.0
                try:
                    # Vendas
                    sel_vendas = [".aleSBU span.AcmPRb", ".v9335u", ".shopee-product-info__header__sold-count"]
                    for sel in sel_vendas:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, sel)
                            texto = elem.text.lower()
                            if "mil" in texto:
                                match_m = re.search(r"(\d+[\d\.,]*)", texto)
                                if match_m:
                                    val_m = match_m.group(1).replace(",", ".")
                                    vendas_count = int(float(val_m) * 1000)
                            else:
                                m_v = re.search(r"(\d+)", texto)
                                if m_v: vendas_count = int(m_v.group(1))
                            if vendas_count > 0: break
                        except: continue

                    # Nota
                    sel_nota = [".F9RHbS.dQEiAI.jMXp4d", "div.shopee-product-rating__rating"]
                    for sel in sel_nota:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, sel)
                            nota = float(elem.text.strip())
                            if nota > 0: break
                        except: continue
                except: pass

                if preco <= 0:
                    print("| ⚠️ Preço atual não identificado. Fechando aba...")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue

                if preco_antigo is None:
                    print("| ⚠️ Sem preço antigo (sem desconto claro). Pulando Shopee...")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue

                # Filtro de Qualidade
                if vendas_count < 100 and preco < 500:
                    print(f"| ❌ REJEITADO: Apenas {vendas_count} vendidos (Mínimo 100 para itens baratos).")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue
                
                print(f"| ✅ APROVADO Shopee: {vendas_count} vendidos | Nota: {nota}")
                
                img_url = None
                try:
                    imgs = driver.find_elements(By.TAG_NAME, "img")
                    for img in imgs:
                        src = img.get_attribute("src")
                        if src and "http" in src and int(img.get_attribute("width") or 0) > 200:
                            img_url = src
                            break
                except: pass

                # GERAR LINK
                print("| 🔗 Clicando em 'Obter link'...")
                link_afiliado = None
                
                try:
                    btn_gerar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.get-link-btn")))
                    btn_gerar.click()
                    time.sleep(2)
                    
                    # Tenta ler do input primeiro (Estratégia A)
                    try:
                        input_link = driver.find_element(By.XPATH, "//input[contains(@value, 'shopee')]")
                        link_afiliado = input_link.get_attribute("value")
                    except:
                        link_afiliado = None

                    # Se falhar, clica em copiar (Estratégia B)
                    if not link_afiliado:
                        btn_copiar = driver.find_element(By.XPATH, "//button[contains(., 'Copiar Link')]")
                        btn_copiar.click()
                        time.sleep(1)
                        link_afiliado = pyperclip.paste()
                    
                except Exception as e:
                    print(f"| ❌ Falha na extração do link: {e}")

                # ============================================================
                # FECHAMENTO SEGURO
                # ============================================================
                print("| 🔙 Fechando aba do produto...")
                
                # Verifica se ainda estamos na aba do produto antes de fechar
                if driver.current_window_handle == aba_produto:
                    driver.close() # Fecha SÓ a aba atual (produto)
                
                driver.switch_to.window(aba_painel) # Volta pra Shopee
                
                if not link_afiliado or "http" not in link_afiliado:
                    print("| ⚠️ Link inválido. Próximo...")
                    continue

                # VALIDAR LINK DE AFILIADO
                if not link_afiliado or not "shope.ee" in link_afiliado:
                    print(f"| ❌ REJEITADO: Link de afiliado inválido ou faltante.")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue

                # FILTROS DE QUALIDADE (TESTE)
                if not titulo or titulo == "Produto Shopee":
                    print(f"| ❌ REJEITADO: Título não capturado corretamente.")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue
                
                if preco <= 0:
                    print(f"| ❌ REJEITADO: Preço zerado ou não capturado.")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue

                if not img_url:
                    print(f"| ❌ REJEITADO: Imagem não capturada.")
                    driver.close()
                    driver.switch_to.window(aba_painel)
                    continue

                # ENVIO
                msg = (
                    f"🔥 <b>ACHADINHO SHOPEE!</b>\n\n"
                    f"📦 <b>{titulo}</b>\n"
                )
                
                if preco_antigo and preco_antigo > preco:
                    desconto = int(((preco_antigo - preco) / preco_antigo) * 100)
                    msg += (
                        f"❌ <s>De: R$ {formatar_preco_br(preco_antigo)}</s>\n"
                        f"✅ <b>Por: R$ {formatar_preco_br(preco)}</b> ({desconto}% OFF) 📉\n"
                    )
                else:
                    msg += f"✅ <b>Apenas: R$ {formatar_preco_br(preco)}</b>\n"
                
                if nota > 0: msg += f"⭐ Avaliação: {nota}/5.0\n"
                
                msg += (
                    f"\n🛒 <b>COMPRE AQUI:</b>\n"
                    f"👉 <a href='{link_afiliado}'>CLIQUE PARA VER</a>"
                )

                enviar_telegram(msg, link_afiliado, img_url)
                
                if img_url:
                    caminho_foto = baixar_imagem_temporaria(img_url)
                    if caminho_foto:
                        enviar_whatsapp_robusto(driver, "Instagram @celle.tech", msg, caminho_foto)
                        os.remove(caminho_foto)
                else:
                    enviar_whatsapp(driver, "Instagram @celle.tech", msg)

                produtos_processados_set.add(titulo)
                # registrar_envio_24h(titulo) # DESATIVADO NO TESTE
                contador_envios += 1

            except Exception as e:
                print(f"| ⚠️ Erro item: {e}")
                # Recuperação de Emergência
                try:
                    # Se tiver mais de 2 abas (Painel + Whats + Erro), tenta fechar a do erro
                    if len(driver.window_handles) > 2:
                        # Tenta identificar qual fechar (a que não é painel nem whats)
                        # Mas por segurança, só volta pro painel se não souber o que fazer
                        driver.switch_to.window(aba_painel)
                    elif len(driver.window_handles) == 2:
                         # Se só tem Painel e Whats, apenas foca no Painel
                         driver.switch_to.window(aba_painel)
                except: pass
                continue

                print(f"| ⚠️ Erro item: {e}")
                # Recuperação de Emergência
                try:
                    # Se tiver mais de 2 abas (Painel + Whats + Erro), tenta fechar a do erro
                    if len(driver.window_handles) > 2:
                        # Tenta identificar qual fechar (a que não é painel nem whats)
                        # Mas por segurança, só volta pro painel se não souber o que fazer
                        driver.switch_to.window(aba_painel)
                    elif len(driver.window_handles) == 2:
                         # Se só tem Painel e Whats, apenas foca no Painel
                         driver.switch_to.window(aba_painel)
                except: pass

    except Exception as e:
        print(f"| ❌ Erro Crítico Shopee: {e}")

def gerar_link_amazon_sitestripe(driver):
    print("| 🔗 AMAZON: Iniciando captura SiteStripe...")
    
    try:
        time.sleep(4) 

        try:
            print("| Procurando botão ID: 'amzn-ss-get-link-button'...")
            
            botao = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "amzn-ss-get-link-button"))
            )
            
            driver.execute_script("arguments[0].click();", botao)
            print("| ✅ Botão CLICADO com sucesso!")
            
        except Exception as e:
            print(f"| ❌ Erro ao clicar no botão: {e}")
            try:
                driver.find_element(By.ID, "amzn-ss-text-link").click()
            except: pass
            return None

        try:
            caixa = WebDriverWait(driver, 8).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#amzn-ss-text-shortlink-textarea, textarea[id*='shortlink']"))
            )
            time.sleep(1.5)
            link_curto = caixa.get_attribute("value")

            if link_curto and "amzn.to" in link_curto:
                print(f"| 🎯 LINK CAPTURADO: {link_curto}")
                
                try:
                    driver.execute_script("document.querySelector('button[class*=\"close-popover\"]').click()")
                except: pass
                
                return link_curto
        except:
            print("| ❌ Botão clicado, mas a caixa de link não apareceu.")
            
    except Exception as e:
        print(f"| ❌ Falha técnica no SiteStripe: {e}")

    return None

def processar_feed_mercadolivre(driver, alvo, produtos_processados_set):
    print(f"\n======== {alvo['nome']} (DETALHADO) ========")
    driver.get(alvo['url_lista'])
    time.sleep(5) 
    
    links_para_visitar = []
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, ".poly-card")
        print(f"| FEED: Encontrei {len(cards)} cards. Coletando links...")
        
        for card in cards[:5]: 
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, "a.poly-component__title")
                url = link_elem.get_attribute("href")
                links_para_visitar.append(url)
            except: continue
    except Exception as e:
        print(f"| Erro ao ler feed: {e}")
        return

    for url_produto in links_para_visitar:
        try:
            driver.get(url_produto)
            
            titulo, preco_atual, preco_antigo, nota, img_url, vendas_count, is_best_seller = extrair_dados_produto_ml(driver)
            
            # --- NOVO FILTRO: MAIS VENDIDOS ---
            if not is_best_seller and vendas_count < 100:
                print(f"| ❌ REJEITADO ML: Apenas {vendas_count} vendidos (Mínimo 100).")
                produtos_processados_set.add(titulo)
                continue
                
            if titulo in produtos_processados_set:
                print(f"| 🚫 DUPLICADO: '{titulo}' já enviado.")
                continue

            print(f"| Analisando: {titulo} | {vendas_count} vendidos / Best Seller: {is_best_seller}")
            
            if produto_eh_bloqueado(titulo):
                print(f"| 🚫 BLOQUEADO: '{titulo}' contém termo proibido.")
                produtos_processados_set.add(titulo)
                continue

            if verificar_se_ja_enviou_24h(titulo):
                print(f"| ⏳ JA ENVIADO (24h): '{titulo}'. Pulando...")
                continue
            print(f"| Preço: R$ {preco_atual} (Antigo: {preco_antigo}) | Nota: {nota}")

            if preco_atual is None: continue

            link_afiliado = gerar_link_ml_via_barra_topo(driver)
            
            if not link_afiliado:
                print("| Pulei: Falha ao gerar link.")
                continue

            emoji = "🔥"
            bloco_preco = f"✅ <b>Por: {formatar_preco_br(preco_atual)}</b>"
            
            if preco_antigo and preco_antigo > preco_atual:
                desconto = int(((preco_antigo - preco_atual) / preco_antigo) * 100)
                bloco_preco = (
                    f"❌ <s>De: {formatar_preco_br(preco_antigo)}</s>\n"
                    f"✅ <b>Por: {formatar_preco_br(preco_atual)}</b> ({desconto}% OFF) 📉"
                )
                emoji = "🚨"

            bloco_nota = ""
            if nota > 4.5: bloco_nota = f"\n⭐ <b>Avaliação: {nota}/5.0</b> (Excelente!)"
            elif nota > 0: bloco_nota = f"\n⭐ <b>Avaliação: {nota}/5.0</b>"

            mensagem = (
                f"{emoji} <b>OFERTA MERCADO LIVRE!</b>\n\n"
                f"📦 <b>{titulo}</b>\n\n"
                f"{bloco_preco}"
                f"{bloco_nota}\n\n"
                f"🛒 <b>COMPRE COM SEGURANÇA:</b>\n"
                f"👉 <a href='{link_afiliado}'>CLIQUE AQUI PARA VER</a>"
            )

            enviar_telegram(mensagem, link_afiliado, img_url)
            
            # --- ENVIO WHATSAPP (TESTE) ---
            try:
                if img_url:
                    caminho_foto = baixar_imagem_temporaria(img_url, "temp_ml.jpg")
                    if caminho_foto:
                        enviar_whatsapp_robusto(driver, "Instagram @celle.tech", mensagem, caminho_foto)
                        human_delay(2, 4)
                        try: os.remove(caminho_foto)
                        except: pass
                    else:
                        enviar_whatsapp(driver, "Instagram @celle.tech", mensagem)
                else:
                    enviar_whatsapp(driver, "Instagram @celle.tech", mensagem)
            except Exception as e_whats:
                print(f"| ❌ Erro ao enviar ML pro Whats: {e_whats}")

            produtos_processados_set.add(titulo)
            registrar_envio_24h(titulo)

        except Exception as e:
            print(f"| ❌ Erro ao processar produto ML: {e}")
            continue

def selecionar_alvos_por_grupo(lista_alvos, grupo):
    return [alvo for alvo in lista_alvos if alvo.get('grupo') == grupo]

def preparar_mensagem_alerta_categoria(nome_categoria):
    nome_categoria_upper = nome_categoria.upper()

    mensagens = {
        "CELULARES": "<b>⚡ Ofertas de Celulares no ar!</b>\nO robô encontrou preços excelentes em smartphones, acessórios e lançamentos. 👇📱✨",
        "GAMES": "<b>🎮🔥 Promoções de Games!</b>\nControles, jogos, cadeiras e acessórios gamer com preço baixo detectado. 👇🔥",
        "PCGAMER": "<b>🖥️⚡ Achados para PC Gamer!</b>\nGabinetes, RAM, SSD, coolers e hardware com descontos reais. 👇💥",
        "TELEVISOES": "<b>📺✨ Ofertas de TVs atualizadas!</b>\nSmart TVs, 4K, 144Hz e modelos premium com preço especial. 👇⚡",
        "BELEZA": "<b>💄✨ Achados de Beleza!</b>\nSkincare, cabelo e perfumaria com descontos verificados pelo robô. 👇🌸",
        "PERIFERICOS": "<b>⌨️🔥 Promoções de Periféricos!</b>\nMouse, teclado, mousepad e teclados mecânicos com preço reduzido. 👇⚡",
        "AUDIO": "<b>🎧💥 Ofertas de Áudio!</b>\nFones, headsets, caixas e soundbars com descontos reais. 👇🔊",
        "MOVEIS": "<b>🪑✨ Ofertas de Móveis!</b>\nMesas, cadeiras, organização e decoração com preço baixo confirmado. 👇🏡",
        "NOTEBOOKS": "<b>💻⚡ Promoções de Notebooks!</b>\nModelos para estudo, trabalho e gamer com quedas de preço. 👇🔥",
        "ELETRODOMESTICOS": "<b>🏠🔥 Ofertas de Eletrodomésticos!</b>\nGeladeira, fogão, lava e seca e muito mais com desconto real. 👇⚡",
        "ELETROPORTATEIS": "<b>⚡✨ Promoções de Eletroportáteis!</b>\nAir fryer, cafeteira, mixer, aspirador e outros com preço reduzido. 👇🔥"
    }
    
    return mensagens.get(nome_categoria_upper, f"<b>✨ Novo Ciclo de Ofertas na Categoria {nome_categoria.capitalize()}!</b> 👇")

def processar_shopee_manual(driver, produtos_processados_set):
    print("\n======== 🟠 SHOPEE (MODO MANUAL) ========")
    arquivo_links = "shopee_links.txt"
    
    if not os.path.exists(arquivo_links):
        print(f"| ⚠️ Arquivo '{arquivo_links}' não encontrado. Adicione links no formato: link|link_afil")
        return

    links_a_processar = []
    with open(arquivo_links, "r", encoding="utf-8") as f:
        linhas = f.readlines()
        for linha in linhas:
            if "|" in linha and not linha.strip().startswith("#"):
                partes = linha.split("|")
                url_prod = partes[0].strip()
                url_afil = partes[1].strip()
                if "http" in url_prod and "http" in url_afil:
                    links_a_processar.append((url_prod, url_afil))

    if not links_a_processar:
        print("| ℹ️ Nenhum link válido no arquivo.")
        return

    aba_navegacao = driver.current_window_handle

    for url_produto, link_afiliado in links_a_processar:
        print(f"\n| --- Processando Link Manual ---")
        try:
            driver.switch_to.window(aba_navegacao)
            driver.get(url_produto)
            time.sleep(5)

            titulo = "Produto Shopee"
            try:
                elem_t = driver.find_element(By.CSS_SELECTOR, ".shopee-product-info__header__title, span.y9e30P, h1")
                titulo = elem_t.text.strip()
            except: pass

            preco = 0.0
            preco_antigo = None
            try:
                for sel in [".IZPeQz.B67UQ0", ".pqTWkA"]:
                    try:
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        val = extrair_valor_numerico(el.text)
                        if val: preco = val; break
                    except: pass
                for sel in [".ZA5sW5", ".v67p8K"]:
                    try:
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        val = extrair_valor_numerico(el.text)
                        if val: preco_antigo = val; break
                    except: pass
            except: pass

            img_url = None
            try:
                imgs = driver.find_elements(By.TAG_NAME, "img")
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and "http" in src and int(img.get_attribute("width") or 0) > 200:
                        img_url = src; break
            except: pass

            # VALIDAÇÃO DE QUALIDADE (MANUAL)
            if not titulo or titulo == "Produto Shopee":
                print(f"| ⚠️ REJEITADO (Manual): Título não capturado.")
                continue
            
            if preco <= 0:
                print(f"| ⚠️ REJEITADO (Manual): Preço não encontrado.")
                continue
            
            if not img_url:
                print(f"| ⚠️ REJEITADO (Manual): Imagem não encontrada.")
                continue

            gatilhos = ["🔥 <b>ACHADINHO!</b>", "😱 <b>BAIXOU MUITO!</b>", "🚨 <b>OFERTA!</b>", "✨ <b>OLHA ISSO!</b>"]
            gatilho = random.choice(gatilhos)
            
            msg = (
                f"{gatilho}\n\n"
                f"📦 <b>{titulo}</b>\n\n"
            )
            
            if preco_antigo and preco_antigo > preco:
                desc = int(((preco_antigo - preco) / preco_antigo) * 100)
                msg += f"❌ <s>De: R$ {formatar_preco_br(preco_antigo)}</s>\n"
                msg += f"✅ <b>Por: R$ {formatar_preco_br(preco)}</b> ({desc}% OFF) 📉\n"
            else:
                msg += f"✅ <b>Preço: R$ {formatar_preco_br(preco)}</b>\n"
            
            msg += (
                f"\n🛒 <b>COMPRE AQUI:</b> 👇\n"
                f"👉 <a href='{link_afiliado}'>CLIQUE PARA VER</a>"
            )

            enviar_telegram(msg, link_afiliado, img_url)
            
            if img_url:
                caminho_foto = baixar_imagem_temporaria(img_url)
                if caminho_foto:
                    enviar_whatsapp_robusto(driver, "Instagram @celle.tech", msg, caminho_foto)
                    if os.path.exists(caminho_foto): os.remove(caminho_foto)
                else:
                    enviar_whatsapp(driver, "Instagram @celle.tech", msg)
            else:
                enviar_whatsapp(driver, "Instagram @celle.tech", msg)

            print(f"| ✅ Enviado com sucesso!")
            time.sleep(3)

        except Exception as e:
            print(f"| ⚠️ Erro: {e}")
            continue

    print("\n| ✅ Fim do processamento manual!")

# =========================================================
# CONFIGURAÇÕES E CREDENCIAIS
# =========================================================

ARQUIVO_HISTORICO =  "historico_precos.csv"
TELEGRAM_BOT_TOKEN = "8221967404:AAEPBsGwc_5oHm71hwvZKf3UCI3A62DYAZk"
TELEGRAM_CHAT_ID = "-1003442405256"

TERMOS_BLOQUEADOS = [
    "controle remoto",
    "freezer horizontal",
    "usado",
    "recondicionado",
    "vitrine",
    "capinha",
    "película",
    "reparo",
    "peça de reposição",
    "caminhão",
    "pneu",
    "peças para"
]

# =====================================================
# LISTAS MESTRAS (ESTRATÉGIA DE GESTOR DE TRÁFEGO)
# =====================================================
LISTA_MESTRE_MAGALU = [
    # --- GRUPO MANHÃ (Foco: Casa, Rotina e Beleza) ---
    {
        "nome": "Magazine Você - Eletroportáteis", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/eletroportateis/l/ep/", 
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "MANHA",
        "categoria": "ELETROPORTATEIS"
    }, 
    {
        "nome": "Magazine Você - Beleza e Perfumaria", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/beleza-perfumaria/l/pf/",
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "MANHA",
        "categoria": "BELEZA"
    },
    {
        "nome": "Magazine Você - Móveis e Escritório", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/moveis/l/mo/",
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "MANHA", # MUDANÇA ESTRATÉGICA: De Tarde para Manhã
        "categoria": "MOVEIS"
    }, 

    # --- GRUPO ALMOÇO (Foco: Pessoal, Impulso e Mobile) ---
    {
        "nome": "Magazine Você - Celulares", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/celulares-e-smartphones/l/te/", 
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "ALMOCO",
        "categoria": "CELULARES"
    },
    {
        "nome": "Magazine Você - Áudio e Som", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/audio/l/ea/",
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "ALMOCO", # MUDANÇA ESTRATÉGICA: De Tarde para Almoço
        "categoria": "AUDIO"
    }, 

    # --- GRUPO TARDE (Foco: Produtividade e Trabalho) ---
    {
        "nome": "Magazine Você - Notebooks", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/notebook/informatica/s/in/note/",
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "TARDE",
        "categoria": "NOTEBOOKS"
    }, 
    {
        "nome": "Magazine Você - Periféricos", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/acessorios-e-perifericos/informatica/s/in/aprf/", 
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "TARDE",
        "categoria": "PERIFERICOS"
    },

    # --- GRUPO NOITE (Foco: Família, Lazer e Gamer Hardcore) ---
    {
        "nome": "Magazine Você - Televisões", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/tv-e-video/l/et/",
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "NOITE",
        "categoria": "TELEVISOES"
    },
    {
        "nome": "Magazine Você - Eletrodomésticos", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/eletrodomesticos/l/ed/",
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "NOITE",
        "categoria": "ELETRODOMESTICOS"
    }, 
    {
        "nome": "Magazine Você - Games (Consoles/Jogos)", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/games/l/ga/", 
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "NOITE", # MUDANÇA ESTRATÉGICA: De Almoço para Noite
        "categoria": "GAMES"
    },
    {
        "nome": "Magazine Você - PC GAMER", 
        "url_lista": "https://www.magazinevoce.com.br/magazinecelle/pc-gamer/informatica/s/in/pcgm/", 
        "dominio_base": "https://www.magazinevoce.com.br",
        "seletor_item_lista": '[data-testid="product-card-container"]', 
        "seletor_link_lista": 'a',
        "seletor_titulo_detalhe": 'h1[data-testid="product-title"]',
        "seletor_preco_detalhe": 'p[data-testid="price-value"]',
        "seletor_preco_antigo": 'p[data-testid="price-original"]',
        "delay_min": 10, "delay_max": 15,
        "grupo": "NOITE",
        "categoria": "PCGAMER"
    }
]

LISTA_MESTRE_AMAZON = [
    # --- MANTIDOS ---
    {
        "nome": "Amazon - Top Eletrônicos",
        "url_lista": "https://www.amazon.com.br/gp/bestsellers/electronics/", 
        "dominio_base": "https://www.amazon.com.br",
        "loja": "AMAZON",
        "seletor_item_lista": 'div[id^="p13n-asin-index-"], div.zg-grid-general-faceout', 
        "seletor_link_lista": 'a.a-link-normal',
        "seletor_titulo_detalhe": '#productTitle',
        "seletor_preco_detalhe": '.a-price .a-offscreen', 
        "seletor_preco_antigo": 'span[data-a-strike="true"] .a-offscreen',
        "delay_min": 5, "delay_max": 10,
        "grupo": "ALMOCO", # Mudado para Almoço
        "categoria": "ELETRONICOS"
    },
    {
        "nome": "Amazon - Computadores",
        "url_lista": "https://www.amazon.com.br/gp/bestsellers/computers/", 
        "dominio_base": "https://www.amazon.com.br",
        "loja": "AMAZON",
        "seletor_item_lista": 'div[id^="p13n-asin-index-"], div.zg-grid-general-faceout', 
        "seletor_link_lista": 'a.a-link-normal',
        "seletor_titulo_detalhe": '#productTitle',
        "seletor_preco_detalhe": '.a-price .a-offscreen', 
        "seletor_preco_antigo": 'span[data-a-strike="true"] .a-offscreen',
        "delay_min": 5, "delay_max": 10,
        "grupo": "TARDE", # Mudado para Tarde
        "categoria": "COMPUTADORES"
    },
    # --- NOVOS (Estratégia de Variedade) ---
    {
        "nome": "Amazon - Mais Vendidos Livros",
        "url_lista": "https://www.amazon.com.br/gp/bestsellers/books/", 
        "dominio_base": "https://www.amazon.com.br",
        "loja": "AMAZON",
        "seletor_item_lista": 'div[id^="p13n-asin-index-"], div.zg-grid-general-faceout', 
        "seletor_link_lista": 'a.a-link-normal',
        "seletor_titulo_detalhe": '#productTitle',
        "seletor_preco_detalhe": '.a-price .a-offscreen', 
        "seletor_preco_antigo": 'span[data-a-strike="true"] .a-offscreen',
        "delay_min": 5, "delay_max": 10,
        "grupo": "MANHA", # Ótimo para começar o dia
        "categoria": "LIVROS"
    },
    {
        "nome": "Amazon - Cozinha",
        "url_lista": "https://www.amazon.com.br/gp/bestsellers/kitchen/", 
        "dominio_base": "https://www.amazon.com.br",
        "loja": "AMAZON",
        "seletor_item_lista": 'div[id^="p13n-asin-index-"], div.zg-grid-general-faceout', 
        "seletor_link_lista": 'a.a-link-normal',
        "seletor_titulo_detalhe": '#productTitle',
        "seletor_preco_detalhe": '.a-price .a-offscreen', 
        "seletor_preco_antigo": 'span[data-a-strike="true"] .a-offscreen',
        "delay_min": 5, "delay_max": 10,
        "grupo": "MANHA", # Pega o público "Dona de Casa"
        "categoria": "CASA"
    },
    {
        "nome": "Amazon - Ferramentas e Construção",
        "url_lista": "https://www.amazon.com.br/gp/bestsellers/hi/", 
        "dominio_base": "https://www.amazon.com.br",
        "loja": "AMAZON",
        "seletor_item_lista": 'div[id^="p13n-asin-index-"], div.zg-grid-general-faceout', 
        "seletor_link_lista": 'a.a-link-normal',
        "seletor_titulo_detalhe": '#productTitle',
        "seletor_preco_detalhe": '.a-price .a-offscreen', 
        "seletor_preco_antigo": 'span[data-a-strike="true"] .a-offscreen',
        "delay_min": 5, "delay_max": 10,
        "grupo": "TARDE", # Público masculino/hobby à tarde
        "categoria": "FERRAMENTAS"
    }
]

LISTA_MESTRE_ML = [
    {
        "nome": "Recomendações ML - Almoço",
        "url_lista": "https://www.mercadolivre.com.br/afiliados/hub#menu-user",
        "loja": "MERCADOLIVRE",
        "categoria": "OFERTAS ML",
        "grupo": "ALMOCO",
        "delay_min": 5, "delay_max": 10,
        "seletor_item_lista": "", "seletor_link_lista": "", "dominio_base": ""
    },
    {
        "nome": "Recomendações ML - Noite",
        "url_lista": "https://www.mercadolivre.com.br/afiliados/hub#menu-user",
        "loja": "MERCADOLIVRE",
        "categoria": "OFERTAS ML",
        "grupo": "NOITE",
        "delay_min": 5, "delay_max": 10,
        "seletor_item_lista": "", "seletor_link_lista": "", "dominio_base": ""
    }
]

LISTA_MESTRE_SHOPEE = [
    {
        "nome": "Shopee - Achadinhos Manhã",
        "url_lista": "https://affiliate.shopee.com.br/offer/product_offer?is_from_login=true", 
        "loja": "SHOPEE",
        "categoria": "ACHADINHOS",
        "grupo": "MANHA",
        "delay_min": 5, "delay_max": 10,
        "dominio_base": "https://shopee.com.br",
        "seletor_item_lista": "", "seletor_link_lista": "" 
    },
    {
        "nome": "Shopee - Achadinhos Tarde",
        "url_lista": "https://affiliate.shopee.com.br/offer/product_offer?is_from_login=true",
        "loja": "SHOPEE",
        "categoria": "ACHADINHOS",
        "grupo": "TARDE", # Adicionado turno Tarde
        "delay_min": 5, "delay_max": 10,
        "dominio_base": "https://shopee.com.br",
        "seletor_item_lista": "", "seletor_link_lista": ""
    },
    {
        "nome": "Shopee - Achadinhos Noite", # Vital para conversão noturna de ticket baixo
        "url_lista": "https://affiliate.shopee.com.br/offer/product_offer?is_from_login=true",
        "loja": "SHOPEE",
        "categoria": "ACHADINHOS",
        "grupo": "NOITE",
        "delay_min": 5, "delay_max": 10,
        "dominio_base": "https://shopee.com.br",
        "seletor_item_lista": "", "seletor_link_lista": ""
    }
]

MAX_PRODUTOS_A_ANALISAR = 5
DOMINIO_BASE = "https://www.magazineluiza.com.br"

chrome_driver = None

def iniciar_driver():
    global chrome_driver
    if chrome_driver is None:
        options = webdriver.ChromeOptions()
        
        # --- TENTA CONEXÃO NO CHROME REAL (OPCIONAL: PARA SHOPEE ANTI-BOT) ---
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        try:
            print("[SISTEMA] Tentando conexão com Chrome aberto na porta 9222 (Modo Anti-Bot)...")
            service = Service(ChromeDriverManager().install())
            chrome_driver = webdriver.Chrome(service=service, options=options)
            print("[SISTEMA] ✅ CONECTADO: Usando sua janela do Chrome carregada.")
        except Exception:
            print("[SISTEMA] ℹ️ Janela 9222 não detectada. Iniciando MODO ISOLADO padrão...")
            # Fallback para o modo antigo se o usuário não abriu o .bat
            options = webdriver.ChromeOptions()
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument(r"--user-data-dir=C:\Users\Camim\whatsapp_selenium_profile")
            options.add_argument("--profile-directory=Default")
            options.add_experimental_option("detach", True)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--start-maximized")

            service = Service(ChromeDriverManager().install())
            chrome_driver = webdriver.Chrome(service=service, options=options)
            chrome_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return chrome_driver

# =========================================================
# FUNÇÕES DE RASTREAMENTO PADRÃO
# =========================================================

def rastrear_lista_produtos(url_lista, driver, seletor_item, seletor_link, dominio_base, max_list_items=5):
    print(f"[SELENIUM] Acessando a lista: {url_lista}")
    driver.get(url_lista)

    if "magazineluiza" in url_lista or "magazinevoce" in url_lista:
        try:
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="cookie-consent-notification-accept"]'))
            )
            cookie_btn.click()
            time.sleep(2) 
        except: pass

    try:
        if "americanas" in url_lista:
            lista_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[title="Forma de exibição horizontal"]'))
            )
            lista_button.click()
            time.sleep(3) 
    except: pass

    try:
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, seletor_item))
        )
    except Exception as e:
        print(f"[ERRO SELENIUM] Tempo limite excedido ou seletor '{seletor_item}' não encontrado. URL: {url_lista}")
        return []
    
    produtos_encontrados = []
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    itens_lista = soup.select(seletor_item)

    print(f"| ENCONTRADOS: {len(itens_lista)} itens na lista. Analisando os {MAX_PRODUTOS_A_ANALISAR} primeiros.")
    
    for i, item in enumerate(itens_lista):
        if i >= max_list_items:
            break

        link_tag = item.select_one(seletor_link)
        if not link_tag and item.name == 'a' and item.get('href'):
            link_tag = item
        if not link_tag:
            link_tag = item.select_one('a[href]')

        if link_tag and link_tag.get('href'):
            url_parcial = link_tag.get('href')
            url_completa = dominio_base + url_parcial if not url_parcial.startswith('http') else url_parcial

            titulo_tag = item.select_one('[data-testid="product-title"]')
            if not titulo_tag:
                titulo_tag = item.select_one('h2') or item.select_one('h3')

            if titulo_tag:
                titulo = titulo_tag.get_text(strip=True)
            else:
                titulo = "Título Desconhecido"
            
            produtos_encontrados.append({
                'titulo': titulo,
                'url': url_completa
            })
    return produtos_encontrados

def rastrear_detalhe_produto(produto, driver, alvo):
    url_produto = produto['url']
    print(f"| Analisando detalhe: {produto['titulo']}")

    try:
        driver.get(url_produto)
    except TimeoutException:
        print(f"[⚠️ TIMEOUT] Produto demorou demais. Pulando.")
        return produto['titulo'], None, None, None, "", False, 0, 0
    except Exception as e:
        print(f"[⚠️ ERRO] Falha ao acessar. Detalhes: {e}")
        return produto['titulo'], None, None, None, "", False, 0, 0

    titulo_final = "Título Desconhecido"
    
    try:
        elemento_titulo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )
        titulo_final = elemento_titulo.text.strip()
    except:
        try:
            titulo_final = driver.execute_script("return document.getElementById('productTitle').innerText").strip()
        except:
            titulo_final = produto['titulo']
            
    print(f"| Título Confirmado: {titulo_final}")

    try:
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)
    except: pass

    soup_detalhe = BeautifulSoup(driver.page_source, 'html.parser')

    preco_atual = None
    preco_antigo = None

    try:
        if "amazon" in url_produto:
            elem_preco = soup_detalhe.select_one('.a-price.aok-align-center .a-offscreen')
            if not elem_preco: elem_preco = soup_detalhe.select_one('.a-price .a-offscreen')
            if not elem_preco: elem_preco = soup_detalhe.select_one('.apexPriceToPay .a-offscreen')
            
            if elem_preco:
                preco_atual = extrair_valor_numerico(elem_preco.get_text())

            elem_antigo = soup_detalhe.select_one('span[data-a-strike="true"] .a-offscreen')
            if elem_antigo:
                preco_antigo = extrair_valor_numerico(elem_antigo.get_text())
        else:
            elem_preco = soup_detalhe.select_one(alvo["seletor_preco_detalhe"])
            if elem_preco:
                preco_atual = extrair_valor_numerico(elem_preco.get_text())
            
            if alvo.get("seletor_preco_antigo"):
                elem_antigo = soup_detalhe.select_one(alvo["seletor_preco_antigo"])
                if elem_antigo:
                    preco_antigo = extrair_valor_numerico(elem_antigo.get_text())
    except Exception: pass

    info_adicional_texto = ""
    try:
        # Busca genérica por texto 'OFF'
        elem_pix = soup_detalhe.find(string=re.compile(r'\d+% OFF'))
        
        if elem_pix: 
            texto_candidato = elem_pix.strip()
            
            # FILTRO DE SANIDADE (EVITAR JSON)
            # 1. Se tiver { ou } ou [ ou ], provavel que é código
            # 2. Se for muito longo (> 50 chars), provavel que é lixo
            if "{" in texto_candidato or "}" in texto_candidato or "[" in texto_candidato:
                pass # Ignora, é código
            elif len(texto_candidato) > 50:
                pass # Ignora, muito longo para ser apenas "10% OFF no Pix"
            else:
                info_adicional_texto = texto_candidato
    except: pass

    image_url = None
    seletores_img = [
        'img[data-testid="image-selected-thumbnail"]',
        'img#landingImage',
        'img[data-a-image-name="landingImage"]',
        'img[data-large-src]',
        'img.main-image'
    ]
    
    for seletor in seletores_img:
        img = soup_detalhe.select_one(seletor)
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-large-src')
            if src and src.startswith('http'):
                image_url = src
                break

    nota_produto = 0.0
    qtd_avaliacoes = 0
    
    try:
        if "amazon" in url_produto:
            elem_nota = soup_detalhe.select_one('span[data-hook="rating-out-of-text"]')
            if not elem_nota: elem_nota = soup_detalhe.select_one('i[data-hook="average-star-rating"] span')
            if elem_nota:
                val = elem_nota.get_text(strip=True).replace(',', '.')
                match = re.search(r'(\d+\.?\d*)', val)
                if match: nota_produto = float(match.group(1))

            elem_qtd = soup_detalhe.select_one('#acrCustomerReviewText')
            if elem_qtd:
                val_q = elem_qtd.get_text(strip=True).replace('.', '')
                match_q = re.search(r'(\d+)', val_q)
                if match_q: qtd_avaliacoes = int(match_q.group(1))
        else:
            elem_nota = soup_detalhe.select_one('[data-testid="review-totalizers-rating"]')
            if not elem_nota: elem_nota = soup_detalhe.select_one('[data-testid="review-score-value"]')
            if elem_nota:
                val = elem_nota.get_text(strip=True).replace(',', '.')
                match = re.search(r'(\d+\.?\d*)', val)
                if match: nota_produto = float(match.group(1))

            elem_qtd = soup_detalhe.select_one('[data-testid="review-totalizers-count"]')
            if not elem_qtd: elem_qtd = soup_detalhe.find('a', string=re.compile(r'avaliaç', re.IGNORECASE))
            if elem_qtd:
                val_q = elem_qtd.get_text(strip=True)
                match_q = re.search(r'(\d+)', val_q)
                if match_q: qtd_avaliacoes = int(match_q.group(1))

        print(f"| QUALIDADE: Nota {nota_produto} | Avaliações: {qtd_avaliacoes}")
    except Exception as e:
        print(f"| WARN: Erro qualidade ({e})")

    eh_relevante = True
    
    # --- NOVO: Lógica de "Mais Vendidos" (Aplica a todas as lojas) ---
    is_best_seller = False
    try:
        # Amazon Best Seller Badge
        if "amazon" in url_produto:
            if soup_detalhe.select_one('.a-badge-text') and "mais vendido" in soup_detalhe.select_one('.a-badge-text').get_text().lower():
                is_best_seller = True
        # Magalu / Generico (procurar selo)
        elif soup_detalhe.find(string=re.compile(r"mais vendido", re.IGNORECASE)):
            is_best_seller = True
    except: pass

    if is_best_seller:
        print(f"| 🏆 BEST SELLER Detectado! Filtro 100+ ignorado.")
    elif qtd_avaliacoes < 100:
        eh_relevante = False
        print(f"| ❌ REJEITADO: Pouca relevância ({qtd_avaliacoes} avaliações, mínimo 100).")
    elif qtd_avaliacoes > 100 and nota_produto < 4.2:
        eh_relevante = False
        print(f"| ❌ REJEITADO: Produto mediano.")
    else:
        print(f"| ✅ APROVADO: Relevância confirmada ({qtd_avaliacoes} avaliações).")

    # --- EXTRAÇÃO DE CUPOM (EXCLUSIVO MAGALU) ---
    cupom_codigo = None
    cupom_valor = None
    if "magazineluiza.com.br" in url_produto or "magazinevoce.com.br" in url_produto:
        try:
            # Tenta pegar o código do cupom (input com data-testid)
            elem_cupom = soup_detalhe.select_one('input[data-testid="coupon-code-input"]')
            if elem_cupom:
                cupom_codigo = elem_cupom.get('value', '').strip()
                print(f"| CUPOM DETECTADO: {cupom_codigo}")
                
                # Tenta pegar o valor do cupom (ex: R$ 200 OFF)
                # O usuário indicou que fica numa div acima do input
                elem_valor_off = soup_detalhe.select_one('div[class*="hwJsdi"] strong')
                if not elem_valor_off:
                    # Fallback: procurar por qualquer strong que contenha 'OFF' perto do cupom
                    div_pai = elem_cupom.find_parent('div')
                    if div_pai:
                        elem_v = div_pai.find('strong', string=re.compile(r'OFF'))
                        if elem_v: cupom_valor = elem_v.get_text(strip=True)
                else:
                    cupom_valor = elem_valor_off.get_text(strip=True)
        except: pass

    return titulo_final, preco_atual, preco_antigo, image_url, info_adicional_texto, eh_relevante, nota_produto, qtd_avaliacoes, cupom_codigo, cupom_valor

def rastrear_cupons(url_cupons, driver):
    """
    Rastreia links de ativação e URLs de imagem de cupons usando Selenium.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando rastreio de cupons (SELENIUM)...")
    
    try:
        driver.get(url_cupons)
        
        SELETOR_CUPOM = "a[data-css-1g36gst]" 
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELETOR_CUPOM))
        )
        
        sopa = BeautifulSoup(driver.page_source, 'html.parser')
        
        cupons_encontrados = []
        
        lista_cupons = sopa.find_all('a', {'data-css-1g36gst': True}) 
        
        for cupom_card in lista_cupons:
            link_ativacao = cupom_card.get('href')
            
            img_tag = cupom_card.find('img')
            img_url = img_tag.get('src') if img_tag else None
            
            descricao = 'Desconto/Oferta especial' 
            if img_url:
                match = re.search(r'pmd_([a-zA-Z0-9]+)_', img_url)
                if match:
                    descricao_raw = match.group(1).upper()
                    descricao = f"Cupom: {descricao_raw}"
                    
            if link_ativacao and img_url: 
                print(f"| DEBUG IMAGE URL: {img_url}")
                cupons_encontrados.append({
                    'link_ativacao': link_ativacao,
                    'descricao': descricao,
                    'imagem_url': img_url
                })

        print(f"[{time.strftime('%H:%M:%S')}] Rastreio de cupons concluído. {len(cupons_encontrados)} cupons encontrados.")
        return cupons_encontrados
        
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO no rastreio de cupons (SELENIUM): {e}")
        return []

    finally:
        pass

def preparar_mensagem_cupons(lista_cupons):
    mensagens_para_envio = []
    for c in lista_cupons:
        mensagem_caption = f"🚨 <b>{c['descricao']}</b> 🚨\n\n"
        mensagem_caption += f"👉 <a href='{c['link_ativacao']}'>CLIQUE AQUI PARA ATIVAR O CUPOM</a>"
        
        mensagens_para_envio.append({
            'mensagem': mensagem_caption,
            'url_link': c['link_ativacao'],
            'image_url': c['imagem_url']
        })
    return mensagens_para_envio

# =========================================================
# FUNÇÕES DE HISTÓRICO E ENVIO
# =========================================================

def atualizar_historico(arquivo_csv, titulo, preco_coletado):
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nova_linha = pd.DataFrame([{'Data': data_hoje, 'Preco': preco_coletado, 'Produto': titulo}])

    try:
        df_existente = pd.read_csv(arquivo_csv)
        df_produto = df_existente[df_existente['Produto'] == titulo]
        if data_hoje not in df_produto['Data'].values:
            df_atualizado = pd.concat([df_existente, nova_linha], ignore_index=True)
            df_atualizado.to_csv(arquivo_csv, index=False)
            print(f"[HISTÓRICO] Preço de {titulo} (R$ {preco_coletado:.2f}) adicionado.")
        else:
            print(f"[HISTÓRICO] Preço de {titulo} já registrado hoje. Sem atualização.")
    except FileNotFoundError:
        nova_linha.to_csv(arquivo_csv, index=False)
        print(f"[HISTÓRICO] Arquivo '{arquivo_csv}' não encontrado. Criando novo.")
    
def analisar_historico(arquivo_csv, titulo, preco_atual, preco_antigo=None):
    try:
        df = pd.read_csv(arquivo_csv)
        df_produto = df[df['Produto'] == titulo].copy()

        oportunidade = False
        veredito = "Dados insuficentes para análise aprofundada."
        menor_preco = preco_atual

        if preco_antigo and preco_antigo > preco_atual:
            desconto = preco_antigo - preco_atual
            desconto_percentual = (desconto / preco_antigo) * 100

            if desconto_percentual >= 10:
                oportunidade = True
                veredito = (
                    f"🔥 SUPER DESCONTO DE BLACK FRIDAY! \n"
                    f"Preço {desconto_percentual:.0f}% abaixo do preço original de R$ {preco_antigo:.2f}."
                )
                return oportunidade, veredito, preco_atual
            
        if df_produto.shape[0] < 5:
            return oportunidade, veredito, preco_atual
        
        df_produto['Data'] = pd.to_datetime(df_produto['Data'])
        df_produto['Preco'] = df_produto['Preco'].astype(float)

        menor_preco_historico = df_produto['Preco'].min()
        media_3m = df_produto.tail(90)['Preco'].mean()

        if preco_atual < menor_preco_historico:
            veredito = f"⭐⭐ COMPRAR AGORA! É o MENOR PREÇO HISTÓRICO (R$ {menor_preco_historico:.2f})."
            oportunidade = True
            menor_preco = menor_preco_historico
        elif preco_atual < media_3m:
            veredito = f"OPORTUNIDADE! Preço (R$ {preco_atual:.2f}) abaixo da média dos últimos 3 meses (R$ {media_3m:.2f})."
            oportunidade = True
            menor_preco = menor_preco_historico
        elif oportunidade == True:
            pass
        else:
            veredito = f"ESPERAR. Preço próximo ou acima da média (R$ {media_3m:.2f}). Não é vantajoso."
            oportunidade = False
            menor_preco = menor_preco_historico

        return oportunidade, veredito, menor_preco
    
    except Exception as e:
        return False, f"Falha na análise: {e}", preco_atual

def enviar_telegram(mensagem_formatada, url_link, image_url=None):
    time.sleep(1)

    if image_url:
        print("[TELEGRAM] Tentando enviar com foto (UPLOAD DE ARQUIVO)...")
        params_photo = {
            'chat_id': TELEGRAM_CHAT_ID,
            'parse_mode': 'HTML',
            'caption': mensagem_formatada
        }

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resposta_img = requests.get(image_url, headers=headers, timeout=10)
            resposta_img.raise_for_status()

            img_bytes = io.BytesIO(resposta_img.content)
            files = {'photo': ('cupom.png', img_bytes)}
            url_api = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'

            resposta = requests.post(url_api, data=params_photo, files=files, timeout=15)
            resposta.raise_for_status()

            print("[TELEGRAM] Mensagem enviada com imagem (upload de arquivo) com sucesso!")
            return
        
        except requests.exceptions.HTTPError as e:
            print(f"[ALERTA] Falha no download ou upload da imagem ({e}). Tentando fallback (sendMessage).")
        except Exception as e:
            print(f"[ALERTA] Erro desconhecido no sendPhoto com upload: {e}. Tentando fallback.")

    print(f"[DEBUG MENSAGEM] Tentando enviar o texto: {mensagem_formatada}")

    print("[TELEGRAM] Enviando como mensagem de texto simples (sendMessage)...")
    params_fallback = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensagem_formatada,
        'parse_mode': 'HTML'
    }

    url_api = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    try:
        resposta = requests.post(url_api, data=params_fallback, timeout=10)
        resposta.raise_for_status()
        print("[TELEGRAM] Mensagem enviada como texto para o grupo com sucesso!")

    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha total ao enviar mensagem para o Telegram> {e}")

def limpar_interface_whatsapp(driver):
    """Garante que não há modais ou caixas de texto abertas travando a interface."""
    # print("| 🧹 Limpando interface do WhatsApp...")
    try:
        action = ActionChains(driver)
        action.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        action.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        
        # Tenta clicar no botão X (fechar) se ele estiver visível
        botoes_fechar = driver.find_elements(By.XPATH, '//span[@data-icon="x-viewer"] | //div[@aria-label="Fechar"] | //span[@data-icon="x"]')
        for btn in botoes_fechar:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
            except: pass
            
    except: pass

def enviar_whatsapp(driver, nome_grupo, mensagem):
    print(f"| 🟢 WHATSAPP: Enviando para o grupo '{nome_grupo}'...")
    
    # --- TROCA PARA A ABA DO WHATSAPP SE NECESSÁRIO ---
    if not focar_aba_whatsapp(driver):
        return

    limpar_interface_whatsapp(driver) # PREVENÇÃO

    try:
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
        )
        
        search_box.click()
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACKSPACE)
        search_box.send_keys(nome_grupo)
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)

        msg_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        
        # LIMPEZA E FOCO
        msg_box.click()
        msg_box.send_keys(Keys.CONTROL + "a")
        msg_box.send_keys(Keys.BACKSPACE)
        human_delay(1, 2) # Pausa antes de começar a 'digitar'

        # Formata a mensagem para o padrão WhatsApp
        msg_final = formatar_para_whatsapp(mensagem)
        
        simular_digitacao(driver, msg_box, msg_final)
        
        human_delay(0.5, 1.2) # Pausa antes de disparar
        msg_box.send_keys(Keys.ENTER)
        
        print(f"| ✅ WHATSAPP: Mensagem enviada com sucesso!")
        human_delay(2, 5) # Delay pós-envio

    except Exception as e:
        print(f"| ❌ WHATSAPP: Falha ao enviar para o grupo: {e}")
    
    finally:
        limpar_interface_whatsapp(driver) # GARANTIA PARA O PRÓXIMO

def enviar_whatsapp_robusto(driver, nome_grupo, mensagem, caminho_imagem):
    print(f"| 📸 WHATSAPP: Iniciando entrega para '{nome_grupo}'...")
    wait = WebDriverWait(driver, 40)
    
    aba_origem = driver.current_window_handle
    
    # --- TROCA PARA A ABA DO WHATSAPP SE NECESSÁRIO ---
    if not focar_aba_whatsapp(driver):
        return

    try:
        limpar_interface_whatsapp(driver) # PREVENÇÃO

        search_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
        search_box.click()
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACKSPACE)
        search_box.send_keys(nome_grupo)
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)

        copiar_imagem_para_clipboard(caminho_imagem)
        chat_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
        chat_box.click()
        # GARANTE QUE NÃO TEM TEXTO PENDENTE
        chat_box.send_keys(Keys.CONTROL + "a")
        chat_box.send_keys(Keys.BACKSPACE)
        time.sleep(1)
        
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

        print("| ⏳ Aguardando editor de legenda...")
        
        # O problema anterior era que ele achava o chat (tab=10) como legenda.
        # Agora o seletor obriga a ser 'Adicionar legenda' OU ter um aria-label que contenha 'legenda'
        # E EXCLUI explicitamente o data-tab=10
        xpath_legenda = '//div[@aria-label="Adicionar legenda"] | //div[contains(@aria-label, "legenda")] | //span[text()="Adicionar legenda"]/../following-sibling::div//div[@contenteditable="true"]'
        
        try:
            legenda_box = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, xpath_legenda))
            )

            # Validação extra: Se o elemento achado for o chat principal, espera mais um pouco
            if legenda_box.get_attribute("data-tab") == "10":
                 print("| ⚠️ Alerta: Seletor pegou o chat principal. Aguardando modal real...")
                 time.sleep(2)
                 legenda_box = driver.find_element(By.XPATH, xpath_legenda)

        except:
             print("| ⚠️ Modal de legenda não identificado pelo nome padrão. Tentando estratégia de focar no elemento ativo...")
             time.sleep(2)
             legenda_box = driver.switch_to.active_element
        
        driver.execute_script("arguments[0].focus();", legenda_box)
        time.sleep(0.5)
        
        # LIMPEZA DA LEGENDA ANTES DE COLAR
        legenda_box.send_keys(Keys.CONTROL + "a")
        legenda_box.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)

        # Formata a mensagem
        msg_final = formatar_para_whatsapp(mensagem)
        pyperclip.copy(msg_final)
        
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        
        human_delay(1, 3)

        print("| 🚀 Disparando o ENVIO...")
        
        # Tenta dar Enter primeiro
        try:
            legenda_box.send_keys(Keys.ENTER)
            human_delay(1, 2)
        except: pass
        
        # Se ainda estiver na tela de imagem (botão enviar ainda lá), tenta clicar no botão
        try:
            # Lista de seletores possíveis para o botão de enviar (inclui data-icon, aria-label e spans)
            seletores_enviar = [
                '//div[@aria-label="Enviar"]',
                '//span[@data-icon="send"]',
                '//button[contains(@aria-label, "Enviar")]',
                '//span[@data-icon="send-light"]/..'
            ]
            
            for seletor in seletores_enviar:
                botoes = driver.find_elements(By.XPATH, seletor)
                if botoes:
                    print(f"| 🎯 Botão 'Enviar' encontrado ({seletor})! Clicando...")
                    driver.execute_script("arguments[0].click();", botoes[0])
                    time.sleep(1)
                    break 
        except Exception as e:
            print(f"| ⚠️ Falha ao clicar no botão físico: {e}")

        # Verificação final: se o modal de imagem ainda estiver aberto, tenta um Enter forçado
        try:
            modal_aberto = driver.find_elements(By.XPATH, '//span[@data-icon="x-viewer"]')
            if modal_aberto:
                print("| 🛠️ Modal ainda aberto. Tentando Enter forçado no elemento ativo...")
                driver.switch_to.active_element.send_keys(Keys.ENTER)
        except: pass

        time.sleep(2) # Espera técnica para o envio iniciar
        print("| ✅ WHATSAPP: Missão cumprida!")

    except Exception as e:
        print(f"| ❌ WHATSAPP: Erro no envio: {e}")
        # Tenta fechar o modal de imagem se estiver aberto (botão X)
        try:
            botao_fechar = driver.find_element(By.XPATH, '//span[@data-icon="x-viewer"]')
            botao_fechar.click()
        except: pass
    
    finally:
        limpar_interface_whatsapp(driver) # GARANTIA DE LIMPEZA
        
        # Volta para a aba que estava antes de tentar enviar (para não quebrar o fluxo principal)
        try:
            driver.switch_to.window(aba_origem)
        except: pass
        print("| 🔄 Voltando para o rastreio...")

# =========================================================
# CONTROLE DE DUPLICIDADE (CACHE 24H)
# =========================================================
ARQUIVO_CACHE_ENVIOS = "cache_envios_24h.json"

def carregar_cache():
    if not os.path.exists(ARQUIVO_CACHE_ENVIOS):
        return {}
    try:
        with open(ARQUIVO_CACHE_ENVIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def salvar_cache(cache):
    try:
        with open(ARQUIVO_CACHE_ENVIOS, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"| ⚠️ Erro ao salvar cache: {e}")

def verificar_se_ja_enviou_24h(titulo):
    """
    Retorna True se o produto já foi enviado nas últimas 24h.
    Se passou de 24h, remove do cache e retorna False (permite envio).
    """
    cache = carregar_cache()
    if titulo not in cache:
        return False
    
    timestamp_envio = cache[titulo]
    agora = time.time()
    
    # 24 horas em segundos = 24 * 60 * 60 = 86400
    if (agora - timestamp_envio) < 86400:
        return True # Ainda está na janela de 24h, bloqueia
    else:
        # Já passou 24h, limpa do cache para permitir novo envio se for detectado
        del cache[titulo]
        salvar_cache(cache)
        return False

def registrar_envio_24h(titulo):
    cache = carregar_cache()
    cache[titulo] = time.time() # Salva o timestamp atual
    salvar_cache(cache)

def main(alvos_a_rodar):
    print("--- ASSISTENTE INTELIGENTE INICIADO ---")

    driver = iniciar_driver()
    
    print(f"| 🌐 Usando instância atual do navegador. Garantindo abas...")
    # Não abrimos nova aba se já estiver conectado ao Chrome real, 
    # pois o usuário já deve ter o WhatsApp aberto lá.
    # Mas vamos garantir que o driver consiga ver o que está aberto.
    print(f"| Abas detectadas: {len(driver.window_handles)}")    
    CATEGORIAS_ALERTADAS = set()
    PRODUTOS_PROCESSADOS_HOJE = set() 

    try:
        for alvo in alvos_a_rodar:

            if alvo.get("loja") == "MERCADOLIVRE":
                processar_feed_mercadolivre(driver, alvo, PRODUTOS_PROCESSADOS_HOJE)
                continue 

            if alvo.get("loja") == "SHOPEE":
                processar_painel_shopee(driver, PRODUTOS_PROCESSADOS_HOJE)
                continue
            
            nome_categoria = alvo['categoria']
            print(f"\n======== {alvo['nome']} ({nome_categoria}) ========")

            tempo_espera = random.randint(alvo['delay_min'], alvo['delay_max'])
            time.sleep(tempo_espera)

            list_limit = 15
            OFERTAS_DINAMICAS = rastrear_lista_produtos(
                alvo['url_lista'], driver, alvo['seletor_item_lista'],
                alvo['seletor_link_lista'], alvo['dominio_base'],
                max_list_items=list_limit
            )

            if not OFERTAS_DINAMICAS: continue
            
            PRODUTOS_VALIDOS = 0
            INDICE = 0
            MAX_TENTAR = 15
            MAX_ANALISAR = 5 

            print(f"| ENCONTRADOS: {len(OFERTAS_DINAMICAS)} itens. Buscando {MAX_ANALISAR} ofertas...")

            while PRODUTOS_VALIDOS < MAX_ANALISAR and INDICE < len(OFERTAS_DINAMICAS) and INDICE < MAX_TENTAR:
                
                produto = OFERTAS_DINAMICAS[INDICE]
                INDICE += 1

                titulo, preco_atual, preco_antigo, image_url, info_adicional, passou_filtro, nota, qtd_reviews, cupom_cod, cupom_val = rastrear_detalhe_produto(
                    produto, driver, alvo
                )

                if not passou_filtro:
                    print(f"| PULANDO: Nota baixa.")
                    continue

                titulo_limpo = titulo.strip()
                
                if produto_eh_bloqueado(titulo_limpo):
                    print(f"| 🚫 BLOQUEADO: '{titulo_limpo}' contém termo proibido.")
                    continue
                
                # --- VERIFICAÇÃO DE CACHE 24H ---
                if verificar_se_ja_enviou_24h(titulo_limpo):
                     print(f"| ⏳ JA ENVIADO (24h): '{titulo_limpo}'. Pulando...")
                     continue
                
                PRODUTOS_PROCESSADOS_HOJE.add(titulo_limpo) # Mantém set local para otimização no loop

                url_final = None
                if alvo.get("loja") == "AMAZON":
                    url_final = gerar_link_amazon_sitestripe(driver)
                    if not url_final:
                        print("| AVISO: SiteStripe falhou, usando link original.")
                        url_final = produto['url']
                else:
                    url_final = gerar_link_afiliado(produto['url'], "MAGALU")

                if preco_atual is None: continue
                if preco_antigo is None:
                    print(f"| PULANDO: Sem preço antigo (desconto não identificado).")
                    continue
                if image_url is None or len(image_url) < 10: continue

                if nome_categoria not in CATEGORIAS_ALERTADAS:
                    msg_head = preparar_mensagem_alerta_categoria(nome_categoria)
                    enviar_telegram(msg_head, None, None)

                    # --- ENVIAR PARA WHATSAPP ---
                    try:
                        enviar_whatsapp(driver, "Instagram @celle.tech", msg_head)
                    except Exception as e:
                        print(f"| ⚠️ Erro ao enviar alerta de categoria no Whats: {e}")
                    # -----------------------------

                    CATEGORIAS_ALERTADAS.add(nome_categoria)
                    time.sleep(2)

                PRODUTOS_VALIDOS += 1
                atualizar_historico(ARQUIVO_HISTORICO, titulo_limpo, preco_atual)
                oportunidade, veredito, menor_preco = analisar_historico(
                    ARQUIVO_HISTORICO, titulo_limpo, preco_atual, preco_antigo=preco_antigo
                )

                print(f"| ENVIANDO: {titulo_limpo} | R$ {preco_atual}")
                
                emoji = "🔥"
                frase = "BAIXOU DE VERDADE!"
                if "MENOR PREÇO" in veredito:
                    emoji = "🚨"
                    frase = "MENOR PREÇO JÁ VISTO!"

                bloco_preco = f"✅ <b>apenas {formatar_preco_br(preco_atual)}</b>"
                if preco_antigo and preco_antigo > preco_atual:
                    desconto = int(((preco_antigo - preco_atual) / preco_antigo) * 100)
                    bloco_preco = (
                        f"❌ <s>de {formatar_preco_br(preco_antigo)}</s>\n"
                        f"✅ <b>por {formatar_preco_br(preco_atual)}</b> ({desconto}% OFF) 📉"
                    )

                bloco_extra = f"\n💳 <i>{info_adicional}</i>" if info_adicional else ""
                
                # --- BLOCO DE CUPOM (MAGALU) ---
                bloco_cupom = ""
                if cupom_cod:
                    val_display = f" ({cupom_val})" if cupom_val else ""
                    bloco_cupom = f"\n\n🎟️ <b>CUPOM: {cupom_cod}</b>{val_display}"

                bloco_stars = ""
                if nota > 0:
                    bloco_stars = f"\n⭐ <b>Nota: {nota}</b> ({qtd_reviews} avaliações)"

                mensagem_final = (
                    f"{emoji} <b>{frase}</b>\n\n"
                    f"📦 <b>{titulo_limpo}</b>\n\n"
                    f"{bloco_preco}"
                    f"{bloco_extra}"
                    f"{bloco_cupom}"
                    f"{bloco_stars}\n\n"
                    f"🛒 <b>COMPRE COM SEGURANÇA:</b>\n"
                    f"👉 <a href='{url_final}'>CLIQUE AQUI PARA VER</a>"
                )

                enviar_telegram(mensagem_final, url_final, image_url)
                
                # Implementar registro no cache após envio bem sucedido
                # registrar_envio_24h(titulo_limpo) # DESATIVADO NO TESTE

                try:
                    caminho_foto = baixar_imagem_temporaria(image_url)
                    if caminho_foto:
                        enviar_whatsapp_robusto(driver, "Instagram @celle.tech", mensagem_final, caminho_foto)
                        os.remove(caminho_foto)
                    else:
                        enviar_whatsapp(driver, "Instagram @celle.tech", mensagem_final)
                except Exception as e_final:
                    print(f"| ❌ Erro final de envio Whats: {e_final}")

    finally:
        driver.quit()
        print("--- FIM DO TURNO ---")

if __name__ == "__main__":

    try:
        ARGUMENTO_PRINCIPAL = sys.argv[1]
    except IndexError:
        ARGUMENTO_PRINCIPAL = "TODOS" 
    
    if ARGUMENTO_PRINCIPAL == "--cupons":
        URL_CUPONS = 'https://especiais.magazineluiza.com.br/magazinevoce/cupons/?showcase=magazinecelle'
        print(f"\n| === MODO CUPONS AGENDADO: {time.strftime('%H:%M:%S')} === |")
        
        driver = iniciar_driver() 
        
        try:
            cupons = rastrear_cupons(URL_CUPONS, driver)
            
            lista_mensagens = preparar_mensagem_cupons(cupons)
            
            if lista_mensagens:
                print(f"| ENVIANDO: Encontrados {len(lista_mensagens)} cupons para envio com imagem.")
                
                for item in lista_mensagens:
                    enviar_telegram(
                        mensagem_formatada=item['mensagem'], 
                        url_link=item['url_link'], 
                        image_url=item['image_url']
                    )
                print("| SUCESSO: Envio de cupons com imagens concluído.")
                
            else:
                print("| NENHUM CUPOM: Nenhum cupom novo encontrado neste turno.")
        
        finally:
            if driver:
                driver.quit()
            
        sys.exit(0)

    else:
        GRUPO_ATUAL = ARGUMENTO_PRINCIPAL.upper()
        LISTA_ALVOS_A_RODAR = []

        if GRUPO_ATUAL == "AMAZON":
            print("📦 MODO DE TESTE: Rodando apenas AMAZON!")
            LISTA_ALVOS_A_RODAR = LISTA_MESTRE_AMAZON

        elif GRUPO_ATUAL == "ML" or GRUPO_ATUAL == "MERCADOLIVRE":
            print("📦 MODO DE TESTE: Rodando apenas MERCADO LIVRE!")
            LISTA_ALVOS_A_RODAR = LISTA_MESTRE_ML

        elif GRUPO_ATUAL == "SHOPEE":
            print("📦 MODO DE TESTE: Rodando apenas SHOPEE (Painel)!")
            LISTA_ALVOS_A_RODAR = LISTA_MESTRE_SHOPEE

        elif GRUPO_ATUAL == "MANUAL":
            print("📝 MODO MANUAL: Processando arquivo shopee_links.txt!")
            driver = iniciar_driver()
            try:
                processar_shopee_manual(driver, set())
            finally:
                if driver: driver.quit()
            sys.exit(0)

        elif GRUPO_ATUAL == "TODOS":
            LISTA_ALVOS_A_RODAR = LISTA_MESTRE_MAGALU + LISTA_MESTRE_AMAZON + LISTA_MESTRE_ML + LISTA_MESTRE_SHOPEE

        else:
            print(f"🕒 Configurando turno: {GRUPO_ATUAL}")
            
            alvos_magalu = selecionar_alvos_por_grupo(LISTA_MESTRE_MAGALU, GRUPO_ATUAL)
            alvos_amazon = selecionar_alvos_por_grupo(LISTA_MESTRE_AMAZON, GRUPO_ATUAL)
            alvos_ml = selecionar_alvos_por_grupo(LISTA_MESTRE_ML, GRUPO_ATUAL)
            alvos_shopee = selecionar_alvos_por_grupo(LISTA_MESTRE_SHOPEE, GRUPO_ATUAL) 
            
            LISTA_ALVOS_A_RODAR = alvos_magalu + alvos_amazon + alvos_ml + alvos_shopee
        
        num_alvos = len(LISTA_ALVOS_A_RODAR)
        print(f"| DEBUG: Encontrados {num_alvos} alvos para o comando '{GRUPO_ATUAL}'.")

        if num_alvos == 0:
            print(f"\n[🛑 ERRO] Nenhuma lista encontrada para '{GRUPO_ATUAL}'.")
            sys.exit(1)

        main(LISTA_ALVOS_A_RODAR)