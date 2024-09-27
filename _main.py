from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import requests
import re
import time
import random

from prisma import Prisma

import logging
import os
from dotenv import load_dotenv


def prisma_reconect():
    prisma.disconnect()
    prisma.connect()


def subir_resolucion(resolucion_archivo):
    headers = {'Accept': 'application/json', API_KEY_NAME: API_KEY}
    url = URL_SUBIR_RESOLUCIONES

    files = {}
    if os.path.isfile(resolucion_archivo):

        archivofinal = open(resolucion_archivo, "rb")

        files['resolucion_archivo'] = (resolucion_archivo, archivofinal)
        try:
            req = requests.post(url, headers=headers, files=files, verify=False)
        except:
            req = None

        if req:
            resultado = req.status_code
        else:
            resultado = -1
    else:
        resultado = -2

    return resultado


def valida_formato_expediente(expediente_pj):
    patron = r'\d{5}-\d{4}-\d+-\d{4}-[A-Z]{2}-[A-Z]{2}-\d{2}'
    return bool(re.fullmatch(patron, expediente_pj))


def configurar_driver():
    """Configura y retorna una instancia de Edge WebDriver."""
    edge_options = Options()
    edge_driver_path = os.path.expanduser('~/Downloads/edgedriver_mac64_m1/msedgedriver')
    service = Service(edge_driver_path)
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def esperar_aleatorio(min_time=0.2, max_time=1.2):
    """Espera por un intervalo de tiempo aleatorio entre min_time y max_time."""
    sleep_time = random.uniform(min_time, max_time)
    print(f"Durmiendo por {sleep_time:.2f} segundos...")
    time.sleep(sleep_time)


def completar_formulario(driver, codigo, captcha):
    """Completa los campos del formulario con el código del expediente y el captcha."""
    ids_campos = ["cod_expediente", "cod_anio", "cod_incidente", "cod_distprov", "cod_organo", "cod_especialidad",
                  "cod_instancia"]

    for i, campo_id in enumerate(ids_campos):
        try:
            driver.find_element(By.ID, campo_id).send_keys(codigo[i])
            esperar_aleatorio()
        except Exception as e:
            logging.info(f"Error al llenar el campo {campo_id}: {e}")

    try:
        driver.find_element(By.ID, "codigoCaptcha").send_keys(captcha)
        esperar_aleatorio()
    except Exception as e:
        logging.info(f"Error al llenar el captcha: {e}")


def obtener_captcha(driver):
    """Obtiene el valor del captcha desde una nueva pestaña."""
    original_window = driver.current_window_handle
    driver.switch_to.new_window('tab')
    driver.get("https://cej.pj.gob.pe/cej/xyhtml")

    try:
        captcha_element = driver.find_element(By.ID, "1zirobotz0")
        captcha_value = captcha_element.get_attribute("value")
    except Exception as e:
        logging.info(f"Error al obtener captcha: {e}")
        captcha_value = None

    driver.close()
    driver.switch_to.window(original_window)
    return captcha_value


def procesar_actuaciones(actuaciones, total_nuevas_actuaciones, soup):
    """Procesa y retorna las nuevas actuaciones extraídas del HTML."""
    lista_nuevas_actuaciones = []
    fechas_principales = ['Fecha de Resolución:', 'Fecha de Ingreso:']

    for acto in actuaciones:
        nro_esquina = acto.find('div', {'class': 'esquina'}).get_text()
        if int(nro_esquina) <= total_nuevas_actuaciones:
            dict_actuacion = {'esquina': nro_esquina}
            registros_datos = acto.findAll('div', {'class': 'borderinf'})

            for detalle_datos in registros_datos:
                etiqueta = detalle_datos.find('div', {'class': 'roptionss'}).get_text().strip() if detalle_datos.find(
                    'div', {'class': 'roptionss'}) else None
                valor = detalle_datos.find('div',
                                           {'class': re.compile('fleft*')}).get_text().strip() if detalle_datos.find(
                    'div', {'class': re.compile('fleft*')}) else ''

                if etiqueta and etiqueta in fechas_principales:
                    dict_actuacion['fecha'] = valor
                elif etiqueta:
                    dict_actuacion[etiqueta.lower().replace(':', '').replace(' ', '_')] = valor

            lista_nuevas_actuaciones.append(dict_actuacion)

    return lista_nuevas_actuaciones


def main(expediente_pj, actuaciones):
    resultado = {}
    codigo = expediente_pj.split("-")

    print(f"Procesando expediente: {expediente_pj}")

    try:
        driver = configurar_driver()
        driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html")

        if not valida_formato_expediente(expediente_pj):
            logging.info("Error en el formato del expediente")
            return

        captcha = obtener_captcha(driver)
        completar_formulario(driver, codigo, captcha)

        try:
            driver.find_element(By.ID, "consultarExpedientes").click()
            esperar_aleatorio()
        except Exception as e:
            logging.info(f"Error al consultar expediente: {e}")

        WebDriverWait(driver, 50).until(EC.visibility_of_element_located((By.ID, 'divDetalles')))

        resumen_expedientes = driver.find_elements(By.CLASS_NAME, "divNroJuz")
        numero_lista = "-".join(codigo[:3]) + "-"
        juzgado = ''
        partes_final = ''

        for expediente_resumen in resumen_expedientes:
            if numero_lista in expediente_resumen.text:
                juzgado = expediente_resumen.text.split('\n')[1]
                partes = driver.find_elements(By.CLASS_NAME, "partesp")
                partes_final = max([parte.text for parte in partes], key=len)
                break

        actuaciones_web = driver.find_elements(By.CLASS_NAME, "esquina")
        nuevas_actuaciones = len(actuaciones_web) > actuaciones

        if nuevas_actuaciones:
            soup = BeautifulSoup(driver.page_source, "lxml")
            total_nuevas_actuaciones = len(actuaciones_web) - actuaciones
            actuaciones_soup = soup.findAll("div", {
                "class": re.compile('panel-body pnl-seg cpnlSeguimiento cpnlSeguimiento*')})

            lista_nuevas_actuaciones = procesar_actuaciones(actuaciones_soup, total_nuevas_actuaciones, soup)
        else:
            lista_nuevas_actuaciones = []

        resultado = {
            "Error": 'OK',
            "Cuadernos": 999,
            "Actuaciones": len(actuaciones_web),
            "Detalle": lista_nuevas_actuaciones,
            "Juzgado": juzgado,
            "Partes": partes_final[:900]
        }

        driver.quit()

    except Exception as e:
        logging.info("Error al abrir Edge")
        logging.error(e)

    return resultado


if __name__ == '__main__':
    load_dotenv()

    # Inicializar y conectar la instancia de Prisma
    prisma = Prisma()
    prisma.connect()

    API_KEY = os.getenv("API_KEY")
    API_KEY_NAME = os.getenv("API_KEY_NAME")
    URL_SUBIR_RESOLUCIONES = os.getenv("URL_SUBIR_RESOLUCIONES")
    URL_ENDPOINT_ENVIA_EMAIL = os.getenv("URL_ENDPOINT_ENVIA_EMAIL")
    URL_ENDPOINT_CONSULTA_AD = os.getenv("URL_ENDPOINT_CONSULTA_AD")
    CARPETA_RESOLUCIONES = os.getenv("CARPETA_RESOLUCIONES")
    LOG_FILE = os.getenv("LOG_FILE")
    pathScript = os.path.realpath(os.path.dirname(__file__))

    expediente = prisma.cej_expedientes.find_first(
        where={
            'activo': 'S',
            'expedientePJ': '00685-2023-0-2801-JR-LA-01'
        },
    )

    print("----- Iniciando Scraping Expediente CEJ -----")
    main(expediente.expedientePJ, expediente.actuaciones)
    print("----- Finalizando Scraping Expediente CEJ -----")

