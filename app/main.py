import sys
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.chrome.service import Service

from bs4 import BeautifulSoup
import requests
import re
import time
import random

from prisma import Prisma
from prisma.models import CEJ_Expedientes,CEJ_ExpedientesUsuarios,CEJ_ProcesoScraping,CEJ_ProcesoScrapingExpedientes,CEJ_ExpedientesActuaciones
from datetime import datetime

import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
import urllib3


def prisma_reconect():
    prisma.disconnect()
    prisma.connect()

def subir_resolucion(resolucion_archivo):
    headers = {'Accept': 'application/json', API_KEY_NAME : API_KEY}
    url = URL_SUBIR_RESOLUCIONES

    files = {}
    if os.path.isfile(resolucion_archivo):
       
        archivofinal = open(resolucion_archivo, "rb")

        files['resolucion_archivo'] = (resolucion_archivo,archivofinal)
        try:
            req = requests.post(url, headers=headers, files=files , verify=False)
        except:
            req = None

        if req:
            resultado = req.status_code
        else:
            resultado = -1
    else:
        resultado = -2

    return resultado    


def valida_formato_expediente(expedientePJ):
  patron = r'\d{5}-\d{4}-\d+-\d{4}-[A-Z]{2}-[A-Z]{2}-\d{2}'
  return bool(re.fullmatch(patron, expedientePJ))

def main(expedientePJ, actuacionesBD, idExpediente):
    min_time = .2  # Tiempo mínimo en segundos
    max_time = 1.2  # Tiempo máximo en segundos

    print(f"Actuaciones de Expediente: {expedientePJ} - {actuacionesBD}")
    
    chrome_options = Options()
        
    # Colocamos la extensión de Chrome/Mozilla    
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.154 Safari/537.36")

    # Evitar la detección de Selenium
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    #chrome_options.add_argument("--headless")  # Ejecutar en modo headless
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    codigo = expedientePJ.split("-")

    try:   
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:      
        logging.info(f"Error al abrir Chrome")
        logging.info(e)

    # Eliminar bandera de automatización de Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.implicitly_wait(1)
    try:
        driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html")
    except Exception as e:
        logging.info(e)

    if valida_formato_expediente(expedientePJ) == False:
        logging.info("Error en el formato")

     # consigue captcha value
    original_window = driver.current_window_handle

    sleep_time = random.uniform(min_time, max_time)
    print(f"Durmiendo por {sleep_time:.2f} segundos...")
    time.sleep(sleep_time)

    driver.switch_to.new_window('tab')
    driver.get("https://cej.pj.gob.pe/cej/xyhtml")

    try:
        xyhtml = driver.find_element(By.ID, "1zirobotz0")

        print(xyhtml)
    except NoSuchElementException:
        logging.info('Error en 1zirobotz0')                  

    valor_captcha = xyhtml.get_attribute("value")

    print(valor_captcha)

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

    try:
        resumen_expedientes = driver.find_elements(By.CLASS_NAME, "divNroJuz")
    except Exception as e:
        logging.info(e)

    numero_lista = codigo[0] + "-" + codigo[1] + "-" + codigo[2] + "-"
    juzgado = ''
    partesFinal = ''

    for expediente in resumen_expedientes:
        if numero_lista in expediente.text:
            juzgado = expediente.text.split('\n')[1]
            partes = driver.find_elements(By.CLASS_NAME, "partesp")
            for parte in partes:
                if len(parte.text)> len(partesFinal):
                    partesFinal = parte.text
            break
        else:
            buscador += 1

    # ingresa a cuaderno
    try:
        botones = driver.find_elements(By.ID, "command")
    except Exception as e:
        logging.info(e)   

    try:
        botones[buscador].click()
    except Exception as e:
        logging.info(e)

    # Copia los cookies de la sesion de Selenium para abrir una sesion con requests
    # la sesion de requests es necesaria para descargar las resoluciones
    s = requests.Session()

    selenium_user_agent = driver.execute_script("return navigator.userAgent;")
    s.headers.update({"user-agent": selenium_user_agent})

    for cookie in driver.get_cookies():
        s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    pagina_html = driver.page_source

    try:
        #soup = BeautifulSoup(pagina_html, "html.parser")
        soup = BeautifulSoup(pagina_html, "lxml")
    except Exception as e:     
        logging.info(e)

    try:
        seguimientos_expediente = driver.find_elements(By.CLASS_NAME, "esquina")
    except Exception as e:
        logging.info(e)

    
    resultado = dict()

    actuaciones_WEB = len(seguimientos_expediente)

    nuevas_actuaciones = actuaciones_WEB >= actuacionesBD
    
    print (f'Actuaciones encontradas :{actuaciones_WEB}')

    if nuevas_actuaciones == True:

        total_nuevas_actuaciones = actuaciones_WEB - actuacionesBD

        actuaciones = soup.findAll("div", {"class" : re.compile('panel-body pnl-seg cpnlSeguimiento cpnlSeguimiento*')})

        lista_nuevas_actuaciones = []

        FechasPrincipales = ['Fecha de Resolución:','Fecha de Ingreso:']

        for actos in actuaciones:
            print ('============================================================================================================')

            nroEsquina = actos.find('div', {'class' : 'esquina'})
            print (f'idExpediente = {idExpediente} - ExpedientePJ = {expedientePJ}')
            print ('ESQUINA:',nroEsquina.get_text())           

            if int(nroEsquina.get_text()) <= total_nuevas_actuaciones:
                                
                # Nueva actuación
                dict_Actuacion = {}
                registrosDatos = actos.findAll('div', {'class' : 'borderinf'})

                dict_Actuacion['esquina'] = nroEsquina.get_text()

                for detalleDatos in registrosDatos:

                    evaluaEtiqueta = detalleDatos.find('div', {'class' : 'roptionss'})
                    evaluaDato = detalleDatos.find('div', {'class' : re.compile('fleft*')})

                    try:
                        etiqueta = evaluaEtiqueta.get_text().strip()
                    except:
                        etiqueta = None

                    try:
                        valor = evaluaDato.get_text().strip()
                    except:
                        valor = ''

                    if etiqueta:
                        if etiqueta in FechasPrincipales:
                            fecha =  valor
                            dict_Actuacion['fecha'] = fecha
                            print ('Fecha:', fecha)

                        if etiqueta == 'Resolución:':
                            resolucion = valor[:79].strip()
                            dict_Actuacion['resolucion'] = resolucion
                            print ('Resolución:', resolucion )

                        if etiqueta == 'Tipo de Notificación:':
                            tiponotificacion = valor[:249].strip()
                            dict_Actuacion['tiponotificacion'] = tiponotificacion
                            print ('Tipo de Notificación:', tiponotificacion )

                        if etiqueta == 'Acto:':
                            acto = valor[:49].strip()
                            dict_Actuacion['acto'] = acto                            
                            print ('Acto:', acto )

                        if etiqueta == 'Fojas:':
                            fojas = valor[:49].strip()
                            dict_Actuacion['fojas'] = fojas  
                            print ('Fojas:', fojas )

                        if etiqueta == 'Proveido:':
                            proveido = valor
                            dict_Actuacion['proveido'] = proveido                              
                            print ('Proveido:', proveido )

                        if etiqueta == 'Descripción de Usuario:':
                            descripcion_usr = valor[:254].strip()
                            dict_Actuacion['descripcion_usr'] = descripcion_usr 
                            print ('Descripción de Usuario:',descripcion_usr)

                        if etiqueta == 'Sumilla:':
                            #sumilla = dato.replace('\n', '')                         
                            sumilla = valor[:999].strip()
                            dict_Actuacion['sumilla'] = sumilla                               
                            print ('Sumilla:', sumilla )                


                # Busca los enlaces con descargas para la actuación, si encuentra descarga archivo

                registrosDescargas = actos.findAll('div', {'class' : 'dBotonDesc'})

                for detalleDescargas in registrosDescargas:
                    archivo = None

                    descarga = detalleDescargas.find('a', {'class' : 'aDescarg'},href=True)
                    
                    if descarga:
                        urlDescarga = descarga['href']
                        print (f'{descarga.text} : {urlDescarga}')
                        
                        # Descarga la resolucion utilizando requests
                        try:

                            archivo = s.get('https://cej.pj.gob.pe/cej/forms/'+urlDescarga)     

                            header = archivo.headers

                            #content_type = header.get('content-type')
                            content_disposition = header.get('content-disposition')
                        except:
                            archivo = None
                            logging.info(f"Error descarga archivo {urlDescarga}")

                if archivo != None:                                
                            try:
                                # Obtiene el nombre del archivo de la resolución a descargar
                                fileResolucion = re.findall("filename=(.+)", content_disposition)[0]

                                print (fileResolucion)
                            except:
                                fileResolucion = ''

                            if fileResolucion != '':
                                fileResolucion = f'{expedientePJ}!{fileResolucion}' 
                                try:
                                    fileResolucionFinal = os.path.join(CARPETA_RESOLUCIONES, fileResolucion)

                                    open(fileResolucionFinal, "wb").write(archivo.content)


                                    if subir_resolucion(fileResolucionFinal) == 200:
                                        dict_Actuacion['resolucion_archivo'] = fileResolucion
                                    else:
                                        print ('ERROR COPIANDO RESOLUCION!')
                                        dict_Actuacion['resolucion_archivo'] = 'error copiado'                                                             
                                except:
                                    dict_Actuacion['resolucion_archivo'] = 'error descarga'

                                print (fileResolucion)

                            else:
                                dict_Actuacion['resolucion_archivo'] = 'error descarga'

                            time.sleep(3)


                lista_nuevas_actuaciones.append(dict_Actuacion)
    else:
        lista_nuevas_actuaciones = []

    resultado["Error"] = 'OK'
    resultado["Cuadernos"] = 999
    resultado["Actuaciones"] = len(seguimientos_expediente)
    resultado["Detalle"] = lista_nuevas_actuaciones                  
    resultado["Juzgado"] = juzgado
    resultado["Partes"] = partesFinal[0:900]

    # CIERRA SELENIUM (3/5/24)
    driver.quit()
    
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

    expediente =  prisma.cej_expedientes.find_first(
            where={
                'activo': 'S',
                'expedientePJ': '11375-2019-0-1801-JR-CA-05'
            },
    )

    print(expediente)

    #main(expediente.expedientePJ, expediente.actuaciones, expediente.idExpediente)