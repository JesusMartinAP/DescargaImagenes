import tkinter as tk
from tkinter import messagebox, scrolledtext
import webbrowser
import requests
from bs4 import BeautifulSoup
import os
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time
import hashlib

# Número máximo de hilos simultáneos
MAX_WORKERS = 10

# Función para abrir el enlace de LinkedIn
def abrir_linkedin():
    webbrowser.open_new("https://www.linkedin.com/in/jesus-apolaya-8814b11b8")

# Función para abrir la carpeta de descargas
def abrir_carpeta_imagenes():
    os.startfile(base_directory)

# Función para calcular el hash de un archivo
def file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

# Función para descargar una imagen con reintentos
def download_image(image_url, filename, folder):
    if not image_url.startswith('http'):
        print(f"URL inválida, se omitirá la descarga: {image_url}")
        return
    
    # Verificar si la imagen ya existe para evitar descargas repetidas
    file_path = os.path.join(folder, filename)
    if os.path.exists(file_path):
        print(f"Imagen ya existe y se omitirá la descarga: {filename}")
        return
    
    retries = 3
    for attempt in range(retries):
        try:
            print(f"Intentando descargar: {image_url}")
            response = requests.get(image_url, timeout=10)
            print(f"Código de estado de la descarga: {response.status_code}")
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print(f"Imagen guardada como: {filename}")
                return
            else:
                print(f"No se pudo descargar la imagen (intento {attempt + 1}).")
        except requests.RequestException as e:
            print(f"Error de solicitud (intento {attempt + 1}): {e}")
        time.sleep(1)  # Espera un segundo antes de reintentar

    print(f"Fallo la descarga de la imagen después de {retries} intentos: {image_url}")

# Función para procesar una URL y descargar imágenes
def process_url(url, folder_name, codigo_padre, downloaded_hashes):
    # Crear la carpeta si no existe
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        
    response = requests.get(url.strip(), timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar todas las imágenes del producto
    image_elements = soup.select('.item img.lazy')

    if image_elements:
        image_number = 1

        for image_element in image_elements:
            image_url = image_element.get('data-src') or image_element.get('src')
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                image_url = 'https://www.marathon.store' + image_url

            # Obtener la URL de la imagen en máxima calidad (2500x2500)
            image_url = image_url.replace('w=1000', 'w=2500').replace('h=1000', 'h=2500')

            if image_url and image_url.startswith('http'):
                print(f"URL de la imagen del producto encontrada: {image_url}")
                # Definir el nombre del archivo con el esquema proporcionado
                filename = f"{codigo_padre}-{image_number}.jpg"
                download_image(image_url, filename, folder_name)
                # Verificar el hash del archivo descargado para evitar duplicados
                file_path = os.path.join(folder_name, filename)
                if os.path.exists(file_path):
                    file_hash_value = file_hash(file_path)
                    if file_hash_value in downloaded_hashes:
                        print(f"Imagen duplicada detectada y eliminada: {filename}")
                        os.remove(file_path)
                    else:
                        downloaded_hashes.add(file_hash_value)
                        image_number += 1
            else:
                print("No se encontró la URL de la imagen del producto o es inválida.")
    else:
        print("No se encontraron elementos de imagen del producto en la página.")

# Función para generar URLs y comenzar la descarga de imágenes
def generar_y_descargar():
    # Crear un conjunto para almacenar hashes de imágenes descargadas
    downloaded_hashes = set()
    lines = text_area.get('1.0', tk.END).strip().split('\n')
    codigos_y_carpetas = [line.split('\t') for line in lines if line]
    pais = country_var.get()

    # Obtener el directorio actual del script
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Crear la carpeta principal con la fecha de hoy
    global base_directory
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    base_directory = os.path.join(script_directory, f"Descarga Img {fecha_hoy}")
    
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    # Crear un ThreadPoolExecutor para gestionar los hilos
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Procesar cada código y carpeta y descargar imágenes en hilos separados
        for codigo, carpeta in codigos_y_carpetas:
            folder_name = os.path.join(base_directory, carpeta)
            url = f"https://www.marathon.store/{pais}/p/{codigo}"
            executor.submit(process_url, url, folder_name, codigo, downloaded_hashes)

    messagebox.showinfo("Descarga Iniciada", "La descarga de imágenes ha comenzado en segundo plano.")

# Configuración de la ventana principal
root = tk.Tk()
root.title("Generador de URLs de Marathon")

# Variable para almacenar el país seleccionado
country_var = tk.StringVar()

# Campo de texto para pegar los códigos y nombres de carpeta
text_area = scrolledtext.ScrolledText(root, height=10)
text_area.pack()

# Botones para seleccionar el país
paises = ['Ecuador', 'Perú', 'Bolivia', 'Chile']
for pais in paises:
    boton = tk.Radiobutton(root, text=pais, variable=country_var, value=pais.lower()[:2], indicatoron=0)
    boton.pack(side=tk.LEFT)

# Botón para generar URLs y descargar imágenes
generar_button = tk.Button(root, text="Descargar Imágenes MARATHON", command=lambda: threading.Thread(target=generar_y_descargar).start())
generar_button.pack(side=tk.BOTTOM, fill=tk.X)

# Botón para abrir la carpeta de imágenes
abrir_carpeta_button = tk.Button(root, text="Abrir Carpeta de Imágenes", command=abrir_carpeta_imagenes)
abrir_carpeta_button.pack(side=tk.BOTTOM, fill=tk.X)

# Etiqueta de hipervínculo para LinkedIn
linkedin_label = tk.Label(root, text="JesusAP", fg="blue", cursor="hand2")
linkedin_label.pack(side=tk.RIGHT, anchor='s')
linkedin_label.bind("<Button-1>", lambda e: abrir_linkedin())

# Ejecutar la aplicación
root.mainloop()
