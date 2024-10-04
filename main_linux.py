from datetime import datetime

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service


from bs4 import BeautifulSoup
import requests
import re
import time
import random

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import requests

from prisma import Prisma

import logging
import os
from dotenv import load_dotenv


def prisma_reconect():
    prisma.disconnect()
    prisma.connect()

def proxies():
    return  {
        'http': f'http://{PROXY_USER}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}',
        'https': f'https://{PROXY_USER}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'
    }

# Configuración de reintento
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2),
       retry=retry_if_exception_type(requests.exceptions.RequestException))
def descargar_archivo(url, s):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ] 

    headers = {
        'User-Agent': f'{random.choice(user_agents)}',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    archivo = s.get(url, headers=headers)
    archivo.raise_for_status()  # Verifica que la respuesta fue exitosa
    return archivo


def guardar_actuaciones_expediente(id_expediente, actuacion, id_proceso):
    date_format_con_hora = '%d/%m/%Y %H:%M'
    date_format_sin_hora = '%d/%m/%Y'

    print("-------- Iniciando guardado de actuación ---------")

    # Obtiene un identificador por cada actuacion para eliminarlo del modelo si es que se encuentra guardado

    idActuacion = actuacion.get('fecha').strip() + actuacion.get('resolucion').strip() + actuacion.get(
        'sumilla').strip()[:200]
    idActuacion = idActuacion.replace(' ', '')

    expediente_actuacion = prisma.cej_expedientesactuaciones.find_first(
        where= {
            'idActuacion': idActuacion,
        }
    )

    if expediente_actuacion:
        print("------------ Actuación ya guardada. ------------")

        return

    if len(actuacion.get('fecha')) > 10:
        try:
            dt_fecha = datetime.strptime(actuacion.get('fecha'), date_format_con_hora)
        except:
            dt_fecha = None
    else:
        try:
            dt_fecha = datetime.strptime(actuacion.get('fecha'), date_format_sin_hora)
        except:
            dt_fecha = None

    if len(actuacion.get('proveido')) > 10:
        try:
            dt_proveido = datetime.strptime(actuacion.get('proveido'), date_format_con_hora)
        except:
            dt_proveido = None
    else:
        try:
            dt_proveido = datetime.strptime(actuacion.get('proveido'), date_format_sin_hora)
        except:
            dt_proveido = None

    now = datetime.now()

    # Inserta la actuacion en el modelo
    prisma.cej_expedientesactuaciones.create(
        data={
            'idActuacion': idActuacion,
            'fecha': dt_fecha,
            'resolucion': actuacion.get('resolucion'),
            'tiponotificacion': actuacion.get('tiponotificacion'),
            'acto': actuacion.get('acto'),
            'proveido': dt_proveido,
            'sumilla': actuacion.get('sumilla'),
            'descripcion_usr': actuacion.get('descripcion_usr'),
            'fojas': actuacion.get('fojas'),
            'resolucion_archivo': actuacion.get('resolucion_archivo'),
            'idExpediente': id_expediente,
            'created_at': now,
            'updated_at': now,
            'idProcesoUltimo': id_proceso,
        },
    )

    print("-------- Finalizando guardado de actuación ---------")

    return


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


def main(expediente_pj, actuaciones_bd, id_expediente):
    global content_disposition, soup, archivo, archivo_resolucion, dict_Actuacion
    min_time = .2  # Tiempo mínimo en segundos
    max_time = 1.2  # Tiempo máximo en segundos
    resultado = dict()

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ] 

    print(f"Actuaciones de Expediente: {expediente_pj} - {actuaciones_bd}")

    codigo = expediente_pj.split("-")

    try:
        firefox_options = Options()
        firefox_options.add_argument("--headless")  

        try:
            driver = webdriver.Firefox(options=firefox_options)
        except Exception as e:
            print(e)

        # Eliminar bandera de automatización de Selenium
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html")
        except Exception as e:
            print(e)    


        if not valida_formato_expediente(expediente_pj):
            logging.info("Error en el formato")

            # consigue captcha value
        original_window = driver.current_window_handle

        sleep_time = random.uniform(min_time, max_time)
        print(f"Durmiendo por {sleep_time:.2f} segundos...")
        time.sleep(sleep_time)

        try:
            driver.switch_to.new_window('tab')
        except Exception as e:
            print(e)    

        try:
            driver.get("https://cej.pj.gob.pe/cej/xyhtml")
        except Exception as e:
            print(e)

        try:
            xyhtml = driver.find_element(By.ID, "1zirobotz0")
        except Exception as e:
            print(e)     


        valor_captcha = xyhtml.get_attribute("value")

        driver.close()
        driver.switch_to.window(original_window)

        # cambia de tab
        try:
            driver.find_element(By.LINK_TEXT, "Por Código de Expediente").click()
            time.sleep(2)
        except Exception as e:
            logging.info(e)

        sleep_time = random.uniform(min_time, max_time)
        print(f"Durmiendo por {sleep_time:.2f} segundos...")
        time.sleep(sleep_time)

        # completa campos del formulario con el codigo de captcha recuperado
        try:
            driver.find_element(By.ID, "cod_expediente").send_keys(codigo[0])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "cod_anio").send_keys(codigo[1])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "cod_incidente").send_keys(codigo[2])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "cod_distprov").send_keys(codigo[3])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "cod_organo").send_keys(codigo[4])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "cod_especialidad").send_keys(codigo[5])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "cod_instancia").send_keys(codigo[6])
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "codigoCaptcha").send_keys(valor_captcha)
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        try:
            driver.find_element(By.ID, "consultarExpedientes").click()
            sleep_time = random.uniform(min_time, max_time)
            print(f"Durmiendo por {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.info(e)

        wait = WebDriverWait(driver, 50)
        element_locator = (By.ID, 'divDetalles')

        try:
            wait.until(EC.visibility_of_element_located(element_locator))
        except Exception as e:
            logging.info(e)

        buscador = 0

        try:
            driver.find_element(By.ID, "divDetalles")
        except Exception as e:
            logging.info(e)

        resumen_expedientes = driver.find_elements(By.CLASS_NAME, "divNroJuz")

        numero_lista = codigo[0] + "-" + codigo[1] + "-" + codigo[2] + "-"
        juzgado = ''
        partesFinal = ''

        for expediente_resumen in resumen_expedientes:
            if numero_lista in expediente_resumen.text:
                juzgado = expediente_resumen.text.split('\n')[1]
                partes = driver.find_elements(By.CLASS_NAME, "partesp")
                for parte in partes:
                    if len(parte.text) > len(partesFinal):
                        partesFinal = parte.text
                break
            else:
                buscador += 1

        botones = driver.find_elements(By.ID, "command")

        botones[buscador].click()

        time.sleep(sleep_time)

        # Copia los cookies de la sesion de Selenium para abrir una sesion con requests
        # la sesion de requests es necesaria para descargar las resoluciones
        s = requests.Session()

        selenium_user_agent = driver.execute_script("return navigator.userAgent;")
        s.headers.update({"user-agent": selenium_user_agent})

        for cookie in driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

        try:
            pagina_html = driver.page_source
        except Exception as e:
            print(e)    

        try:
            soup = BeautifulSoup(pagina_html, "lxml")
        except Exception as e:
            print(e)

        seguimientos_expediente = driver.find_elements(By.CLASS_NAME, "esquina")

        actuaciones_WEB = len(seguimientos_expediente)

        nuevas_actuaciones = actuaciones_WEB >= actuaciones_bd

        if nuevas_actuaciones:
            total_nuevas_actuaciones = actuaciones_WEB - actuaciones_bd

            actuaciones = soup.findAll("div",
                                       {"class": re.compile('panel-body pnl-seg cpnlSeguimiento cpnlSeguimiento*')})

            lista_nuevas_actuaciones = []

            FechasPrincipales = ['Fecha de Resolución:', 'Fecha de Ingreso:']

            for actos in actuaciones:
                print('=======================================================================')
                nroEsquina = actos.find('div', {'class': 'esquina'})
                print('Esquina:', nroEsquina.get_text())
                print("Total nuevas actuaciones:", total_nuevas_actuaciones)

                if int(nroEsquina.get_text()) <= total_nuevas_actuaciones:
                    # Nueva actuación
                    dict_Actuacion = {}

                    registrosDatos = actos.findAll('div', {'class': 'borderinf'})

                    dict_Actuacion['esquina'] = nroEsquina.get_text()

                    for detalleDatos in registrosDatos:

                        evaluaEtiqueta = detalleDatos.find('div', {'class': 'roptionss'})
                        evaluaDato = detalleDatos.find('div', {'class': re.compile('fleft*')})

                        try:
                            etiqueta = evaluaEtiqueta.get_text().strip()
                        except (Exception, AttributeError):
                            etiqueta = None

                        try:
                            valor = evaluaDato.get_text().strip()
                        except (Exception,):
                            valor = ''

                        if etiqueta:
                            if etiqueta in FechasPrincipales:
                                fecha = valor
                                dict_Actuacion['fecha'] = fecha

                            if etiqueta == 'Resolución:':
                                resolucion = valor[:79].strip()
                                dict_Actuacion['resolucion'] = resolucion

                            if etiqueta == 'Tipo de Notificación:':
                                tiponotificacion = valor[:249].strip()
                                dict_Actuacion['tiponotificacion'] = tiponotificacion

                            if etiqueta == 'Acto:':
                                acto = valor[:49].strip()
                                dict_Actuacion['acto'] = acto

                            if etiqueta == 'Fojas:':
                                fojas = valor[:49].strip()
                                dict_Actuacion['fojas'] = fojas

                            if etiqueta == 'Proveido:':
                                proveido = valor
                                dict_Actuacion['proveido'] = proveido

                            if etiqueta == 'Descripción de Usuario:':
                                descripcion_usr = valor[:254].strip()
                                dict_Actuacion['descripcion_usr'] = descripcion_usr

                            if etiqueta == 'Sumilla:':
                                # sumilla = dato.replace('\n', '')
                                sumilla = valor[:999].strip()
                                dict_Actuacion['sumilla'] = sumilla

                # Busca los enlaces con descargas para la actuación, si encuentra descarga archivo
                botones_descarga = actos.findAll('div', {'class': 'dBotonDesc'})

                if len(botones_descarga) > 0:
                    for detalle_descarga in botones_descarga:
                        archivo = None
                        descarga = detalle_descarga.find('a', {'class': 'aDescarg'}, href=True)

                        if descarga:
                            url = descarga['href']

                            if url is not None and url != '':
                                try:
                                    form_url = 'https://cej.pj.gob.pe/cej/forms/' + url
                                    # Usamos la función de reintento para descargar el archivo
                                    archivo = descargar_archivo(form_url, s)

                                    header = archivo.headers
                                    content_disposition = header.get('content-disposition')

                                    # Si tenemos el content-disposition, procesamos el nombre del archivo
                                    if content_disposition:
                                        archivo_resolucion = re.findall("filename=\"?([^\";]+)\"?", content_disposition)
                                        if archivo_resolucion:
                                            archivo_resolucion = archivo_resolucion[0]
                                            archivo_resolucion = f'{expediente_pj}{archivo_resolucion.strip()}'
                                        else:
                                            archivo_resolucion = None
                                    else:
                                        archivo_resolucion = None

                                    # Si no hay nombre de archivo en content-disposition, usar la URL
                                    if not archivo_resolucion:
                                        archivo_resolucion = os.path.basename(
                                            url)  # Extrae el último fragmento de la URL como nombre del archivo
                                        archivo_resolucion = f'{expediente_pj}{archivo_resolucion.strip()}'

                                    # Guardar el archivo
                                    archivo_resolucion_final = os.path.join(CARPETA_RESOLUCIONES, archivo_resolucion)
                                    with open(archivo_resolucion_final, 'wb') as f:
                                        f.write(archivo.content)
                                    print(f'Archivo guardado correctamente en: {archivo_resolucion_final}')
                                    dict_Actuacion['resolucion_archivo'] = archivo_resolucion_final
                                    guardar_actuaciones_expediente(id_expediente, dict_Actuacion, id_expediente)


                                except requests.exceptions.RequestException as e:
                                    dict_Actuacion['resolucion_archivo'] = f'error descarga: {e}'
                                    print(f'Error en la descarga: {e}')
                            else:
                                print("URL no válida para la descarga")
                        else:
                            dict_Actuacion['resolucion_archivo'] = None
                            print("No se encontró el botón de descarga")


                        # Pausa para evitar sobrecargar el servidor
                        time.sleep(sleep_time)

                guardar_actuaciones_expediente(id_expediente, dict_Actuacion, id_expediente)
                lista_nuevas_actuaciones.append(dict_Actuacion)
                driver.quit()
        else:
            lista_nuevas_actuaciones = []

        resultado["Error"] = 'OK'
        resultado["Cuadernos"] = 999
        resultado["Actuaciones"] = len(seguimientos_expediente)
        resultado["Detalle"] = lista_nuevas_actuaciones
        resultado["Juzgado"] = juzgado
        resultado["Partes"] = partesFinal[0:900]

        driver.quit()
    except Exception as e:
        logging.info(f"Error al abrir Edge")
        logging.info(e)

    return resultado


def actualizar_expediente(id_expediente, actuaciones_bd, juzgado, partes):
    print("----- Actualizando Expediente -----")

    now = datetime.now()

    update = prisma.cej_expedientes.update(
        where={
            'idExpediente': id_expediente
        },
        data={
            'actuaciones': actuaciones_bd,
            'juzgado': juzgado,
            'partes': partes,
            'updated_at': now
        }
    )
    return update


try:
    if __name__ == '__main__':
        print("----- Iniciando Scraping Expediente CEJ -----")
        load_dotenv()
        prisma = Prisma()
        prisma.connect()

        API_KEY = os.getenv("API_KEY")
        API_KEY_NAME = os.getenv("API_KEY_NAME")
        URL_SUBIR_RESOLUCIONES = os.getenv("URL_SUBIR_RESOLUCIONES")
        URL_ENDPOINT_ENVIA_EMAIL = os.getenv("URL_ENDPOINT_ENVIA_EMAIL")
        URL_ENDPOINT_CONSULTA_AD = os.getenv("URL_ENDPOINT_CONSULTA_AD")
        CARPETA_RESOLUCIONES = os.getenv("CARPETA_RESOLUCIONES")
        PROXY_HOST = os.getenv("PROXY_HOST")
        PROXY_PORT = os.getenv("PROXY_PORT")
        PROXY_USER = os.getenv("PROXY_USER")
        PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
        LOG_FILE = os.getenv("LOG_FILE")
        pathScript = os.path.realpath(os.path.dirname(__file__))

        print("Prisma conectado")

        expedientes = prisma.cej_expedientes.find_many(
            where={'activo': 'S'},
        )
        print(f"Expedientes encontrados: {len(expedientes)}")

        for expediente in expedientes:
            actuaciones = main(expediente.expedientePJ, expediente.actuaciones, expediente.idExpediente)
            if actuaciones.get("Actuaciones") is not None:
                actualizar_expediente(expediente.idExpediente, actuaciones.get('Actuaciones'),
                                      actuaciones.get('Juzgado'), actuaciones.get('Partes'))
            print("----- Finalizando Scraping Expediente CEJ -----")

except Exception as e:
    print(f"Ocurrió un error: {e}")
