import requests
from bs4 import BeautifulSoup
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------- Lista de equipos -----------------------
TEAMS = {
    "Racing Club": "https://www.sofascore.com/es/equipo/futbol/racing-club/3215",
    "Huracán": "https://www.sofascore.com/es/equipo/futbol/huracan/7629",
    "Independiente": "https://www.sofascore.com/es/equipo/futbol/independiente/3209",
    "Tigre": "https://www.sofascore.com/es/equipo/futbol/tigre/7628",
    "Rosario Central": "https://www.sofascore.com/es/equipo/futbol/rosario-central/3217",
    "Argentinos Juniors": "https://www.sofascore.com/es/equipo/futbol/argentinos-juniors/3216",
    "Estudiantes de La Plata": "https://www.sofascore.com/es/equipo/futbol/estudiantes-de-la-plata/3206",
    "San Lorenzo": "https://www.sofascore.com/es/equipo/futbol/san-lorenzo/3201",
    "Boca Juniors": "https://www.sofascore.com/es/equipo/futbol/boca-juniors/3202",
    "River Plate": "https://www.sofascore.com/es/equipo/futbol/river-plate/3211",
}

# ----------------------- Función para obtener los enlaces de los jugadores -----------------------
def get_players_links(team_url):
    response = requests.get(team_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    players_links = set()
    for link in soup.find_all('a', href=True):
        if '/jugador/' in link['href']:
            full_url = f"https://www.sofascore.com{link['href']}"
            players_links.add(full_url)
    return list(players_links)

# ----------------------- Función para extraer minutos y goles de un jugador -----------------------
def es_numero(valor):
    try:
        return float(valor) if '.' in valor else int(valor)
    except ValueError:
        return None

def get_player_stats(player_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(player_url)
    time.sleep(5)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    spans = soup.find_all("span")

    # Buscar la posición del primer span que contenga "2025"
    start_index = next((i for i, span in enumerate(spans) if "2025" in span.text.strip()), None)

    # Si no encuentra "2025", devolver 0 en todo
    if start_index is None:
        return 0, 0

    # Cortar la lista de spans desde "2025" en adelante
    spans = spans[start_index:]

    # Detectamos hasta dónde tomar los spans (antes de "Leyenda")
    for i, span in enumerate(spans):
        if "Leyenda" in span.text.strip():
            spans = spans[:i]
            break

    suma_minutos, suma_goles = 0, 0
    i = 0
    while i < len(spans):
        valor = es_numero(spans[i].text.strip())
        if isinstance(valor, float):  
            target_index = i + 3  
            if target_index + 1 < len(spans):
                minutos = es_numero(spans[target_index].text.strip())
                goles = es_numero(spans[target_index + 1].text.strip())
                if isinstance(minutos, int) and isinstance(goles, int):
                    suma_minutos += minutos
                    suma_goles += goles
                    i = target_index + 2  
                    continue
        i += 1

    return suma_minutos, suma_goles

# ----------------------- Código principal -----------------------
CSV_FILENAME = "jugadores_estadisticas.csv"

with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["EQUIPO", "LINK_JUGADOR", "MINUTOS", "GOLES", "GOLES CADA 90 MIN"])

    for team_name, team_url in TEAMS.items():
        print(f"\n🔍 Procesando equipo: {team_name}")
        players = get_players_links(team_url)

        for player_url in players:
            minutos, goles = get_player_stats(player_url)
            goles_por_90 = round((goles / minutos) * 90, 2) if minutos > 0 else 0

            writer.writerow([team_name, player_url, minutos, goles, goles_por_90])
            print(f"✅ {player_url} | Min: {minutos} | Goles: {goles} | Goles/90: {goles_por_90}")

print(f"\n✅ Datos guardados en {CSV_FILENAME}")
