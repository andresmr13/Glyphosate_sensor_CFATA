# Programa Control V6,
# Programa para tomar datos de entrenamiento de redesd neuronales
# Se integra proceso de medicion de luz dispersada y luz emitida.
# Se homologa para que sea exactamente la misma metodologia para medir datos de entrenamiento y medicion molecular
# Elaborado por Alejandro Gimenez, 20 Julio 2024
# Esta version recibe datos seleccionados (100) para tener mejor resolucion y tener una red neuronal de tamañol viable para ESP32.


# Importa dependencias
import serial
import numpy as np
import matplotlib.pyplot as plt
#import time
import tkinter as tk
#from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
#from datetime import datetime
from PIL import ImageGrab
from PIL import Image, ImageTk
import sys

# Constantes para la proporción de la ventana
BASE_WIDTH = 1200
BASE_HEIGHT = 900
ASPECT_RATIO = BASE_WIDTH / BASE_HEIGHT

# global is_measurement_busy

is_measurement_busy = False

# Declaraciones globales
ser = serial.Serial()
ser.baudrate = 115200
#ser.port = 'COM3' #Cambiar dependiendo del puerto usado 
ser.port = '/dev/cu.usbserial-0001' # Este es el puerto en mi mac @Andres.                         

conectado = False # Esta variable nos dice si esta conectado o no
limploty = 300 # Limite de grafica en intensidad

# Variables para guardar los valores de Tint, Gan y Temp
EstTint = 700
EstGan = 16
EstTemp = 20.00
EstVolt = 7.2           

# Arreglo de datos Dispersion
DisResults = np.zeros(288, dtype=int)
EmiResults = np.zeros(288, dtype=int)

# Tasa de sondeo para la batería (en milisegundos)
# n segundos = n * 1000
VBAT_POLL_RATE_MS = 10000 # 10 segundos

# Funcion para guardar datos de las mediciones
def GuardaDato(datos):
    # Define the file path
    file_path = 'datosDisEmi.csv'
    # Check if the file already exists
    file_exists = False
    try:
        with open(file_path, 'r') as file:
            file_exists = True
    except FileNotFoundError:
        pass

    # Append data to the CSV file
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        # Write data rows
        writer.writerow(datos)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
def conectar():
    # Inicio de comunicacion////////////////////////////////////////////////////////////////////////////////////////////////////
    print(ser)
    print(ser.is_open)

    if (ser.is_open == False):
        ser.open()

    #ser.flushInput()
    recibe = ""
    while (recibe != b'CONOK\r\n'):
        ser.flushInput()
        ser.write(b'CHCON\n')
        recibe = ser.readline()
        print(recibe)
        recibe = ser.readline()
        print(recibe)

    print("Conectado")
    botCon.configure(bg="red", fg="white") 
    # Ahora esta línea solo actualiza el texto y color de la *segunda* etiqueta
    labConStatus.config(text="Conectado", fg="green")

    botCon.config(state="disabled")
    botLdon.config(state="normal")
    botLason.config(state="normal")
    botonDE.config(state="normal")
    botonSaveSpec.config(state="normal") 
    botonSaveIm.config(state="normal") 
    botVbat.config(state="normal")
    botATI.config(state="normal")

    # Configura alto tiempo de integracion y ganancia
    ajutint()
    
    # Inicia el sondeo automático de la batería
    poll_vbat_loop()

# Ajuste de tiempo de integracion
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
def ajutint():
    ser.flushInput()
    #strparaati="AjTiIn"
    vti = tbati.get('1.0', tk.END)
    vtid3 = int(int(vti))
    strparati = "AjHTI" + str(vtid3) + "\n"
    bobj = bytes(strparati, 'utf-8')
    ser.write(bobj)
    #recibe=ser.readline()
    print(strparati)
    # Para guardar dato de tiempo de integracion
    global EstTint
    EstTint = int(vti)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
def med_espect(esopt):
    # Crea lista con longitudes desde 340 a 850
    longs = np.linspace(340, 850, 50)    #288
    bar_labels = np.linspace(340, 850, 50)  #288
    colorbars = np.array([wavelength_to_rgb(w) for w in longs])
   
    # Hace medicion y grafica valores.
    ser.flushInput()
    #ser.write(b'MVAL\n')      #Medicion de uno solo
    ser.write(b'MVal\n')      #Medicion de 10 datos, antes era MVX10

    recibe = ser.readline()
    print(recibe)
    recibe = ser.readline()
    input_string = recibe

    # Decode the bytes to a string and split it by commas
    values_str = input_string.decode('utf-8').split(',')
    # Convert the string values to floating-point numbers
    values_float = [float(value) for value in values_str if value.strip()]
    # Convert the list to a numpy array
    result_array = np.array(values_float)

    # Obtiene valor maximo del array de resultados
    intmaxsen = result_array.max()
    intminsen = result_array.min()
   
    # Increase the width of the figure
    fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6

    if (esopt == 3):
        fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the width (12 inches in this example)    #12,6

    ax.scatter(longs, result_array, color=colorbars, label=bar_labels)
    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)

    if (esopt == 1):
        ax.set_title('Espectro Dispersion')
        plt.xticks(fontsize=7)

    if (esopt == 2):
        ax.set_title('Espectro Emision')
        plt.xticks(fontsize=7)

    if (esopt == 3):
        ax.set_title('Espectro')  
        plt.xticks(fontsize=10) 

    limploty = int(tblim.get('1.0', tk.END))
    # Checa si es autolimite o no
    if (cheal_state.get() == True):
        limplotya = int(intmaxsen * 1.2)
        limplotyb = int(intminsen * 0.6)
        if intmaxsen == 0:
            intmaxsen = 1
    
    # Fija el limite de y 
    ax.set_ylim(limplotyb, limplotya)

    # Para dibujarlo en la ventana del GUI
    # Embed the Matplotlib plot in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    #canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    if (esopt == 1):
        canvas_widget.place(x=0, y=40)

    if (esopt == 2):
        canvas_widget.place(x=600, y=40)  

    if (esopt == 3):
        canvas_widget.place(x=0, y=40)   

    #root.plt.show()
    print("otro")
    global DisResults
    global EmiResults

    if (esopt == 1):
        DisResults = result_array

    if (esopt == 2):
        EmiResults = result_array

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Hace las dos graficas de una vez
def grafDE(valoresD, valoresE):
    # Tablas de longitudes de onda y etiquetas
    longs = np.linspace(340, 850, 50)    #288
    bar_labels = np.linspace(340, 850, 50)   #288
    colorbars = np.array([wavelength_to_rgb(w) for w in longs])

    # grafica valores.
    # Hace un numpy array de los datos de dispersion
    values_float = valoresD
    result_arrayD = np.array(values_float)

    # Obtiene valor maximo del array de resultados
    intmaxsen = result_arrayD.max()
    intminsen = result_arrayD.min()

    # Increase the width of the figure
    fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6
    ax.scatter(longs, result_arrayD, color=colorbars, label=bar_labels)
    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)
    ax.set_title('Espectro Dispersion')
    plt.xticks(fontsize=7)
    
    limplotyb = int(intmaxsen * 1.2)
    limplotya = 0                                      #int(intminsen*0.6)
    ax.set_ylim(limplotya, limplotyb)

    # Para dibujarlo en la ventana del GUI
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.place(x=0, y=40)       #Para dispersion poner en 600,40

    # Hace un numpy array de los datos de emision
    values_float = valoresE
    result_arrayE = np.array(values_float)

    # Obtiene valor maximo del array de resultados
    intmaxsen = result_arrayE.max()

    # Increase the width of the figure
    fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6
    ax.scatter(longs, result_arrayE, color=colorbars, label=bar_labels)
    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)
    ax.set_title('Espectro Emision')
    plt.xticks(fontsize=7)
    
    limplotyb = int(intmaxsen * 1.2)
    limplotya = 0                                #int(intminsen*0.6)
    ax.set_ylim(limplotya, limplotyb)

    # Para dibujarlo en la ventana del GUI
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.place(x=600, y=40)       #Para dispersion poner en 600,40
   
    #root.plt.show()

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //// GUARDA IMAGEN DE ESPECTROSCOPIA
def guaIma():
    inivenx = root.winfo_x()
    iniveny = root.winfo_y() + 75
    finvenx = int(inivenx + 1200)
    finveny = int(iniveny + 600)
    screenshot = ImageGrab.grab(bbox=(inivenx, iniveny, finvenx, finveny))
    # Save the screenshot as an image
    nombrearchivo = tbNombre.get("1.0", "end-1c") + '.png'
    screenshot.save(nombrearchivo)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
def guardado():
    nombremed = tbNombre.get("1.0", "end-1c")
    concmed = tbConc.get("1.0", "end-1c")

    datosMed = [nombremed, concmed, "---"]
    datosMed.extend(DisResults)
    datosMed.extend("-")
    datosMed.extend(EmiResults)

    print(datosMed)
    GuardaDato(datosMed)

    # --- AÑADIDO ---
    # 3. Rehabilita el botón cuando la medición termina.
    print("Medición finalizada.")
    botonDE.config(state="normal")
    # (Opcional: podrías actualizar una etiqueta de "Midiendo..." a "Listo")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# /// CICLO DE MEDICION DISPERSION Y EMISION
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# def MedDE():
def _MedDE_execute():
    global DisResults, EmiResults, is_measurement_busy
    
    try:
        # Manda comando para medir Glifosato
        ser.flushInput()
        ser.write(b'SCAN\n')

        # Primera linea es el acknoledge
        recibe = ser.readline()
        print(recibe)
    
        # La segunda linea son los valores de dispersion
        recibe = ser.readline()
        input_string = recibe
        values_str = input_string.decode('utf-8').split(',')
        values_float = [float(value) for value in values_str if value.strip()]
        result_array = np.array(values_float)
        DisResults = result_array
        mediD = result_array

        # La tercera linea son los valores de emision
        recibe = ser.readline()
        input_string = recibe
        values_str = input_string.decode('utf-8').split(',')
        values_float = [float(value) for value in values_str if value.strip()]
        result_array = np.array(values_float)
        EmiResults = result_array
        mediE = result_array

        # Grafica datos
        grafDE(mediD, mediE)

        # Guarda datos
        guardado()

        # Recibe resultado de medicion en instrumento
        recibe = ser.readline()
        print(recibe)
        recibe = ser.readline()
        print(recibe)
        #recibe=ser.readline()
        #print(recibe)

    except Exception as e:
        # Es una buena práctica registrar cualquier error
        print(f"Error durante la medición MedDE: {e}")

    finally:
        # --- AÑADIDO ---
        # 2. Libera el candado, sin importar si la medición
        #    tuvo éxito o falló.
        is_measurement_busy = False
        
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //// FUNCIONES DE BOTONES DE CONTROL (LEDs, Laser, Batería)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ... (justo después de VBAT_POLL_RATE_MS) ...
# 1. Esta es la NUEVA función MedDE que tu botón llama.

def MedDE():
    # --- AÑADIDO ---
    global is_measurement_busy 
    # --- FIN ---

    print("Iniciando retraso de 15 segundos...")
    
    # --- CORRECCIÓN ---
    # 1. Poner el candado AHORA, al inicio del retraso.
    is_measurement_busy = True 

    # --- FIN ---
    # --- AÑADIDO ---
    # Deshabilita el botón "Medir D/E" para evitar clics múltiples
    botonDE.config(state="disabled")
    
    # (Opcional: aquí podrías poner una etiqueta que diga "Midiendo en 15s...")

    # Programa la ejecución de _MedDE_execute después de 15000 ms (15 seg)
    root.after(15000, _MedDE_execute)


def on_resize(event):
    """Mantiene la proporción de la ventana cuando se redimensiona."""
    
    # Prevenir bucles de eventos si nuestra propia llamada a .geometry() dispara el evento
    if (event.width, event.height) == root.last_set_size:
        return

    # Calcular la altura objetivo basada en el ancho actual
    target_height = int(event.width / ASPECT_RATIO)
    
    # Calcular el ancho objetivo basado en la altura actual
    target_width = int(event.height * ASPECT_RATIO)

    # Decidir qué dimensión es la "limitante"
    # Esto mantiene la ventana *dentro* del arrastre del mouse
    if target_height > event.height:
        # La altura es el factor limitante
        final_width = target_width
        final_height = event.height
    else:
        # El ancho es el factor limitante
        final_width = event.width
        final_height = target_height

    # Guardar el tamaño que estamos a punto de establecer
    root.last_set_size = (final_width, final_height)
    root.geometry(f"{final_width}x{final_height}")

def midvbat():
    """Ejecuta una sola medición de batería y actualiza la GUI."""
    if not ser.is_open:
        labVbat.config(text="N/C") # No Conectado
        print("Intento de medir VBAT sin conexión")
        return

    try:
        ser.flushInput()
        ser.write(b'MBAT\n')
        
        recibe_ack = ser.readline() # ACK
        print(f"MBAT ACK: {recibe_ack}")
        recibe_val = ser.readline() # Valor
        print(f"MBAT RECV: {recibe_val}")

        # Decodificar y limpiar el valor (ej. b'7.2\r\n' -> '7.2')
        volt_str = recibe_val.decode('utf-8').strip()

        if volt_str: # Asegurarse que no esté vacío
            #labVbat.config(text=f"{volt_str} V") # <-- LÍNEA MODIFICADA
            global EstVolt
            EstVolt = float(volt_str)
            print(f"Voltaje actualizado: {EstVolt} V")
            if EstVolt<7.3:
                print("Voltaje bajo, cargar bateria.")
                bat_color = 'red'
            else:
                bat_color = 'green'
            labVbat.config(text=f"{EstVolt:.2f} V", fg=bat_color)

            
        else:
            labVbat.config(text="N/A") # No disponible
    
    except serial.SerialException as se:
        print(f"Error de Serial en midvbat: {se}") #"Error de Serial en midvbat: {se}"
        labVbat.config(text="E01")
    except ValueError as ve:
        print(f"Error de conversión de valor en midvbat: {ve} (recibido: {recibe_val})")#Error de conversión de valor en midvbat: {ve} (recibido: {recibe_val})"
        labVbat.config(text="E02")
    except Exception as e:
        print(f"Error inesperado en midvbat: {e}")#"Error inesperado en midvbat: {e}"
        labVbat.config(text="E03")

def poll_vbat_loop():
    """Función que se llama periódicamente para medir la batería."""
    if ser.is_open and not is_measurement_busy: 
        # --- FIN DE LA MODIFICACIÓN ---
            midvbat()
    
    # Reprogramar la próxima ejecución
    root.after(VBAT_POLL_RATE_MS, poll_vbat_loop)

# //// PRENDE Y APAGA LUZ DIFUSA
def DisLedOn():
    ser.flushInput()
    ser.write(b'DISLEDON\n')
    recibe = ser.readline()
    print(recibe)
    labLEDStatus.config(text="ON", fg="green")
    botLdon.config(state="disabled")
    botLdoff.config(state="normal")

def DisLedOff():
    ser.flushInput()
    ser.write(b'DISLEDOFF\n')
    recibe = ser.readline()
    print(recibe)
    labLEDStatus.config(text="OFF", fg="red")
    botLdoff.config(state="disabled")
    botLdon.config(state="normal")

# //// PRENDE Y APAGA LASER (750mA)
def LasOn():
    #labLaserStatus = tk.Label(root, text="OFF", fg='red')
    ser.flushInput()
    ser.write(b'LasOn\n')
    recibe = ser.readline()
    print(recibe)
    labLaserStatus.config(text="ON", fg="green")
    botLason.config(state="disabled")
    botLasoff.config(state="normal")

def LasOff():
    ser.flushInput()
    ser.write(b'LasOff\n')
    recibe = ser.readline()
    print(recibe)
    labLaserStatus.config(text="OFF", fg="red")
    botLasoff.config(state="disabled")
    botLason.config(state="normal")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
def alcerrar():
    ser.close()
    # Pone parametros en default
    root.destroy()

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
def wavelength_to_rgb(wavelength):
    gamma = 0.8
    intensity_max = 255

    if wavelength < 380 or wavelength > 750:
        return (0, 0, 0)  # Wavelength out of range

    if 380 <= wavelength < 440:
        R = -(wavelength - 440) / (440 - 380)
        G = 0.0
        B = 1.0
    elif 440 <= wavelength < 490:
        R = 0.0
        G = (wavelength - 440) / (490 - 440)
        B = 1.0
    elif 490 <= wavelength < 510:
        R = 0.0
        G = 1.0
        B = -(wavelength - 510) / (510 - 490)
    elif 510 <= wavelength < 580:
        R = (wavelength - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif 580 <= wavelength < 645:
        R = 1.0
        G = -(wavelength - 645) / (645 - 580)
        B = 0.0
    elif 645 <= wavelength <= 750:
        R = 1.0
        G = 0.0
        B = 0.0
    else:
        R = G = B = 0

    # Intensity correction
    if 380 <= wavelength < 420:
        SSS = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
    elif 645 <= wavelength <= 750:
        SSS = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
    else:
        SSS = 1.0

    R = round(intensity_max * ((R * SSS) ** gamma))
    G = round(intensity_max * ((G * SSS) ** gamma))
    B = round(intensity_max * ((B * SSS) ** gamma))

    return (R / 255, G / 255, B / 255)  # Normalize RGB values to [0, 1]

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ///  Diseño grafico del GUI
# Ventana principal/////////////////////////////////////////////////////////////////////////////////////////////
# Abre ventana, para usarse como GUI
root = tk.Tk()
# Pone el nombre de la ventana
root.title("Control de equipo sensor Glifosato")
# Ajusta el tamaño y lo deja fijo 
root.geometry("1200x800")

try:
    # Check the operating system
    if 'darwin' in sys.platform:
        # MAC: Requires a .icns file
        # Make sure 'my_icon.icns' is in the same folder
        root.iconbitmap("icon.icns") 
    else:
        # WINDOWS: Requires a .ico file
        root.iconbitmap("icon.ico")
        
except Exception as e:
    print(f"No se pudo cargar el icono: {e}")

# --- AÑADIR ESTAS LÍNEAS ---
#
#  Guardar el tamaño inicial para nuestra función de redimensión
#root.last_set_size = (BASE_WIDTH, BASE_HEIGHT)
# Vincular el evento de redimensión a nuestra función
#root.bind("<Configure>", on_resize)
# --- FIN DEL AÑADIDO ---

# root.minsize(1200, 900) # set minimum window size value
# root.maxsize(1200, 900) # set maximum window size value

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Botones de Conexion, mediciones y guardado

# --- AÑADIDO: Etiqueta de estado de conexión ---
# Etiqueta 1: El texto estático que NO cambia de color
labConStatic = tk.Label(root, text="Status de conexión:", fg="black") 
labConStatic.place(x=470, y=8)

# Etiqueta 2: El texto dinámico que SÍ cambia de color
labConStatus = tk.Label(root, text="Sin conexión", fg="red")
labConStatus.place(x=590, y=8) # 'x' está ajustado para que aparezca después de la etiqueta 1
# --- FIN DEL AÑADIDO ---
# 
# # Botones de Conexion, mediciones y guardado
# Declara boton
botCon = tk.Button(root, text="Conectar", command=conectar)
botCon.place(x=700, y=5)

# Boton de hacer medicion dispersion, 
botonDE = tk.Button(root, text="Medir D/E", command=MedDE)
botonDE.place(x=20, y=650)
botonDE.config(state="disable")

# Boton de guardar emision, 
botonSaveSpec = tk.Button(root, text="Espectro", command=lambda: med_espect(3))
botonSaveSpec.place(x=120, y=650)
botonSaveSpec.config(state="disable")

# Boton para guardar imagen de espectroscopia, 
botonSaveIm = tk.Button(root, text="Guardar Imagen", command=guaIma)
botonSaveIm.place(x=220, y=650)
botonSaveIm.config(state="disable")

# Ajuste de tiempo de integracion
tbati = tk.Text(root, height=1, width=4)
tbati.insert(tk.END, "50")
tbati.place(x=700, y=665)
labati2 = tk.Label(root, text="ms")
labati2.place(x=725, y=663)

# Ajuste de tiempo de integracion
botATI = tk.Button(root, text="Ajustar", command=ajutint)
botATI.place(x=755, y=658)
botATI.config(state="disable")

# Etiqueta de rango de valores permitidos
labati = tk.Label(root, text="Tiempo de integración: (1-250 ms)")#1-250 mS")
labati.place(x=700, y=640)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Ventanas para meter datos de medicion
# Nombre de la medicion
labNombre = tk.Label(root, text="Nombre Medicion")
labNombre.place(x=20, y=720)
tbNombre = tk.Text(root, height=1, width=14)
tbNombre.place(x=20, y=740)
tbNombre.insert(tk.END, "Nombre")

# Concentracion molecular
labConc = tk.Label(root, text="Concentracion [ppm]")
labConc.place(x=170, y=720)
tbConc = tk.Text(root, height=1, width=8)
tbConc.place(x=170, y=740)
tbConc.insert(tk.END, "0.0")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Ajuste de limites? de graficacion en y
cheal_state = tk.IntVar(value=1)
cheal = tk.Checkbutton(root, text="Auto ajuste Y", variable=cheal_state)
cheal.place(x=700, y=840)

tblim = tk.Text(root, height=1, width=6)
tblim.insert(tk.END, "300")
tblim.place(x=800, y=845)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Mide Bateria
pos_x_boton = 960
separacion_boton_etiqueta = 110 # <-- ¡Ajusta esta 'distancia' como quieras!

botVbat = tk.Button(root, text="Medir", command=midvbat)
botVbat.place(x=pos_x_boton+50, y=658)
botVbat.config(state="disabled") # <-- AÑADIR ESTA LÍNEA

labVbat = tk.Label(root, text="Nivel de batería:")
labVbat.place(x=pos_x_boton, y=630+10)

labVbat = tk.Label(root, text="-----")
labVbat.place(x=pos_x_boton, y=663)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# PRENDE/APAGA LUZ DIFUSA
labLED = tk.Label(root, text="Control del LED:")
labLED.place(x=450, y=630+10)
labLEDStatus = tk.Label(root, text="OFF", fg='red')
labLEDStatus.place(x=560, y=630+10)

botLdon = tk.Button(root, text="LED On", command=DisLedOn)
botLdon.place(x=450, y=650+10)

botLdoff = tk.Button(root, text="LED Off", command=DisLedOff)
botLdoff.place(x=530, y=650+10)
botLdoff.config(state="disabled") # <-- AÑADIR ESTA LÍNEA
botLdon.config(state="disabled")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# PRENDE/APAGA LASER
labLaser = tk.Label(root, text="Control del laser:")
labLaser.place(x=450, y=680+10)
labLaserStatus = tk.Label(root, text="OFF", fg='red')
labLaserStatus.place(x=565, y=680+10)

botLason = tk.Button(root, text="Laser On", command=LasOn)
botLason.place(x=450, y=700+10)

botLasoff = tk.Button(root, text="Laser Off", command=LasOff)
botLasoff.place(x=540, y=700+10)
botLasoff.config(state="disabled") # <-- AÑADIR ESTA LÍNEA
botLason.config(state="disabled")


# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Desplienga en la GUI logos: UNAM, CFATA Y CONACYT
# Carga las imagenes
orimage1 = Image.open("LogoCFATA.png")  
width, height = 120, 60  # Set the desired width and height for the resized image
image1 = orimage1.resize((width, height))
photo1 = ImageTk.PhotoImage(image1)
portalogo1 = tk.Label(root, image=photo1)
portalogo1.place(x=900, y=800-80)

orimage2 = Image.open("secihti_logo.jpg")  
width, height = 150, 60  # Set the desired width and height for the resized image
image2 = orimage2.resize((width, height))
photo2 = ImageTk.PhotoImage(image2)
portalogo2 = tk.Label(root, image=photo2)
portalogo2.place(x=900+125, y=800-80)

# Pone en pantalla relacion de intensidades
#labRatio=tk.Label(root,text="560/645")
#labRatio.place(x=460,y=830)

# Cuando se cierra la ventana se corre una rutina
root.protocol("WM_DELETE_WINDOW", alcerrar)
root.mainloop()