import requests
from bs4 import BeautifulSoup
import csv
import time
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Desactivar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lista de equipos y URLs
TEAMS = {
    "Racing Club": "https://www.sofascore.com/es/equipo/futbol/racing-club/3215",
    "Huracán": "https://www.sofascore.com/es/equipo/futbol/huracan/7629",
    "Independiente": "https://www.sofascore.com/es/equipo/futbol/independiente/3209",
    "Tigre": "https://www.sofascore.com/es/equipo/futbol/tigre/7628",
    "Rosario Central": "https://www.sofascore.com/es/equipo/futbol/rosario-central/3217",
    "Argentinos Juniors": "https://www.sofascore.com/es/equipo/futbol/argentinos-juniors/3216",
    "Estudiantes de La Plata": "https://www.sofascore.com/es/equipo/futbol/estudiantes-de-la-plata/3206",
    "San Lorenzo": "https://www.sofascore.com/es/equipo/futbol/san-lorenzo/3201",
    "Central Córdoba": "https://www.sofascore.com/es/equipo/futbol/central-cordoba/65676",
    "Defensa y Justicia": "https://www.sofascore.com/es/equipo/futbol/defensa-y-justicia/36839",
    "Barracas Central": "https://www.sofascore.com/es/equipo/futbol/barracas-central/65668",
    "Deportivo Riestra": "https://www.sofascore.com/es/equipo/futbol/deportivo-riestra/189723",
    "Lanús": "https://www.sofascore.com/es/equipo/futbol/lanus/3218",
    "Platense": "https://www.sofascore.com/es/equipo/futbol/platense/36837",
    "Independiente Rivadavia": "https://www.sofascore.com/es/equipo/futbol/independiente-rivadavia/36842",
    "Gimnasia y Esgrima de La Plata": "https://www.sofascore.com/es/equipo/futbol/gimnasia-y-esgrima/3205",
    "Belgrano": "https://www.sofascore.com/es/equipo/futbol/belgrano/3203",
    "Banfield": "https://www.sofascore.com/es/equipo/futbol/banfield/3219",
    "Godoy Cruz": "https://www.sofascore.com/es/equipo/futbol/godoy-cruz/6074",
    "Unión": "https://www.sofascore.com/es/equipo/futbol/club-atletico-union/3204",
    "Instituto Córdoba": "https://www.sofascore.com/es/equipo/futbol/instituto-cordoba/4937",
    "Sarmiento": "https://www.sofascore.com/es/equipo/futbol/sarmiento/42338",
    "Newell's Old Boys": "https://www.sofascore.com/es/equipo/futbol/newells-old-boys/3212",
    "Vélez Sarsfield": "https://www.sofascore.com/es/equipo/futbol/velez-sarsfield/3208",
    "Talleres de Córdoba": "https://www.sofascore.com/es/equipo/futbol/talleres/3210",
    "Atlético Tucumán": "https://www.sofascore.com/es/equipo/futbol/atletico-tucuman/36833",
    "San Martín de San Juan": "https://www.sofascore.com/es/equipo/futbol/san-martin-de-san-juan/7772",
    "Aldosivi": "https://www.sofascore.com/es/equipo/futbol/aldosivi/36836",
    "Boca Juniors": "https://www.sofascore.com/es/equipo/futbol/boca-juniors/3202",
    "River Plate": "https://www.sofascore.com/es/equipo/futbol/river-plate/3211"
}

# Función para obtener enlaces de jugadores
def get_players_links(team_url):
    response = requests.get(team_url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')

    players_links = set()
    for link in soup.find_all('a', href=True):
        if '/jugador/' in link['href']:
            players_links.add(f"https://www.sofascore.com{link['href']}")

    return list(players_links)

# Función para extraer minutos y goles usando Selenium
def get_player_stats(player_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(player_url)
    time.sleep(3)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    spans = soup.find_all("span")[70:200]

    minutos, goles = 0, 0
    for i in range(len(spans) - 3):
        try:
            if spans[i].text.strip().isdigit():
                if spans[i+3].text.strip().isdigit() and spans[i+4].text.strip().isdigit():
                    minutos += int(spans[i+3].text.strip())
                    goles += int(spans[i+4].text.strip())
        except:
            continue

    # Calcular goles cada 90 minutos
    if minutos > 0:
        goles_por_90 = (goles / minutos) * 90
    else:
        goles_por_90 = 0

    return minutos, goles, goles_por_90

# Función para extraer el nombre del jugador desde el enlace
def get_player_name(player_url):
    # El nombre está en la URL en la forma "/jugador/nombre-apellido/id"
    player_id = player_url.split("/")[4]  # Parte del enlace después de "/jugador/"
    player_name = player_id.replace("-", " ").title()  # Reemplaza "-" con espacio y usa title() para capitalizar
    return player_name

# Archivo de salida CSV
CSV_FILENAME = "jugadores_estadisticas.csv"

with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["EQUIPO", "JUGADOR", "link_jugador", "minutos", "goles", "goles_por_90"])

    for team_name, team_url in TEAMS.items():
        print(f"\n🔍 Procesando equipo: {team_name}")
        players = get_players_links(team_url)

        for player_url in players:
            player_name = get_player_name(player_url)
            minutos, goles, goles_por_90 = get_player_stats(player_url)
            writer.writerow([team_name, player_name, player_url, minutos, goles, goles_por_90])
            print(f"✅ {player_name} | Minutos: {minutos} | Goles: {goles} | Goles por 90: {goles_por_90:.2f}")

print(f"\n✅ Datos guardados en {CSV_FILENAME}")
