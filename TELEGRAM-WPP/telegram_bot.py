import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---- CONFIG TELEGRAM ----
BOT_TOKEN = "8221967404:AAEPBsGwc_5oHm71hwvZKf3UCI3A62DYAZk"
CHANNEL_ID = "-1003442405256"
URL_GET_UPDATES = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

# ---- CONFIG WHATSAPP ----
WHATSAPP_GROUP_NAME = "PromoClick • Operação Black Friday 🚨"

# ---- CONFIG CHROME ----
PROFILE_PATH = r"C:\Projetos\BlackFridayAssistant\ChromeProfile"

def iniciar_whatsapp():
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")  # mantém login
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    
    # ChromeDriver Manager instala e usa a versão certa automaticamente
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get("https://web.whatsapp.com/")

    print("📲 Escaneie o QR Code do WhatsApp (só na primeira vez)...")

    try:
        XPATH_CONVERSAS_VISIVEL = '//div[@id="pane-side"]'
        wait = WebDriverWait(driver, 60)
        wait.until(EC.visibility_of_element_located((By.XPATH, XPATH_CONVERSAS_VISIVEL)))
        print("✅ WhatsApp Web carregado e pronto para uso.")
    except Exception as e:
        print("🚨 WhatsApp não carregou. Verifique QR Code ou conexão.")
        driver.quit()
        raise e

    return driver

def enviar_no_whatsapp(driver, texto):
    try:
        wait = WebDriverWait(driver, 30)

        # Localiza a barra de pesquisa de conversas
        XPATH_BUSCA = '//div[@data-testid="search-input"]'
        caixa_busca = wait.until(EC.presence_of_element_located((By.XPATH, XPATH_BUSCA)))
        caixa_busca.click()
        caixa_busca.send_keys(WHATSAPP_GROUP_NAME)
        time.sleep(2)
        caixa_busca.send_keys(Keys.ENTER)
        time.sleep(2)

        # Localiza a caixa de mensagem
        XPATH_MENSAGEM = '//div[@contenteditable="true"][@role="textbox"]'
        caixa_msg = wait.until(EC.presence_of_element_located((By.XPATH, XPATH_MENSAGEM)))
        caixa_msg.click()
        caixa_msg.send_keys(texto)
        caixa_msg.send_keys(Keys.ENTER)
        print("➡️ Mensagem enviada para o WhatsApp!")

    except Exception as e:
        print(f"🚨 Erro ao enviar no WhatsApp: {e}")

def pegar_atualizacoes(offset):
    response = requests.get(URL_GET_UPDATES, params={"offset": offset})
    dados = response.json()
    return dados.get("result", [])

def iniciar_bridge():
    driver = iniciar_whatsapp()
    last_update_id = None

    while True:
        updates = pegar_atualizacoes(last_update_id)
        for update in updates:
            last_update_id = update["update_id"] + 1
            if "channel_post" in update:
                texto = update["channel_post"].get("text")
                if texto:
                    print("📥 Recebido no Telegram:", texto)
                    enviar_no_whatsapp(driver, texto)
        time.sleep(2)

if __name__ == "__main__":
    iniciar_bridge()
