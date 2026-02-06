# Programa para Interfaz gráfica con ESP32 corriendo rutina de medición y predicción de glifosato.
# Se integra proceso de medicion de dispersión de luz blanca (LED) y luz emitida (con exitación IR).
# Se homologa para que sea exactamente la misma metodologia para medir datos de entrenamiento y medicion molecular
# Elaborado por Alejandro Gimenez, 20 Julio 2024
# Esta version recibe datos seleccionados (100).

# El código ha sido modificado por Andres Montes de Oca a partir de Oct, 2025.
# Se incorporan botones para el control manual del LED y el laser. También se incluye un botón para realizar la conexión
# y una leyenda que muestra el estado de conexión.
# Se agregó un temporizador al botón de mediciones (aprox. 15 s).
# También se muestra el nivel de batería que se actualiza cada vez que se toma una medición

# Modulos
import serial
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
from PIL import ImageGrab
from PIL import Image, ImageTk

ser = serial.Serial()
ser.baudrate = 115200
#ser.port = 'COM3' # Usualmente se detecta como un COM en PCs
ser.port = '/dev/cu.usbserial-0001' # Este es el puerto en mi mac @Andres.                     

conectado = False # Esta variable nos dice si esta conectado o no
medicion_en_progreso = False # Semáforo para evitar colisiones en el puerto serial
limploty = 300 # Limite de grafica en intensidad

# Variable para monitorear el widget actual y asi poder borrarlo antes de dibujar uno nuevo
current_canvas_widget = None

# Variables para guardar los valores de Tint (tiempo de integración), Gan (ganancia) y Temp (temperatura)
# Iniciales
EstTint = 700
EstGan = 16
EstTemp = 20.00
EstVolt = 7.2           

# Arreglo de datos para guardar dispersión y emisión
DisResults = np.zeros(288, dtype=int)
EmiResults = np.zeros(288, dtype=int)

# función para recibir datos por serial
def parse_serial_data(raw_bytes, expected_length=50):
    """
    Decodifica bytes en el puerto serial de manera segura, ignora basura (\xff), 
    y asegura que el arreglo de salida coincida con la dimensión del eje X.
    """
    try:
        text_data = raw_bytes.decode('utf-8', errors='ignore')
        # Limpia espacios en blanco
        text_data = text_data.strip()
        
        # Se filtran caracteres validos: digitos, comas, puntos, signo negativo)
        clean_chars = [c for c in text_data if c in "0123456789.-,"]
        clean_text = "".join(clean_chars)
        
        # Se separan los datos
        values_str = clean_text.split(',')
        values_float = []
        for v in values_str:
            try:
                if v: # check if not empty
                    values_float.append(float(v))
            except ValueError:
                continue

        # Se forza el tamaño del arreglo a 50
        y_array = np.array(values_float)
        
        if len(y_array) != expected_length:
            print(f"T_MSG: Warning - Received {len(y_array)} points, expected {expected_length}. Resizing...")
            current_x = np.linspace(0, 1, len(y_array))
            target_x = np.linspace(0, 1, expected_length)
            y_array = np.interp(target_x, current_x, y_array)

        return y_array

    except Exception as e:
        print(f"T_MSG: Error parsing data: {e}")
        # Regresa un arreglo de ceros para evitar error
        return np.zeros(expected_length)

# Función para conectarse con el ESP32   
def conectar():
    """
    Rutina para establecer conexión con el sensor.
    """
    # Verificación del puerto serial
    if not ser.is_open:
        try:
            ser.open()
        except serial.SerialException as e:
            print(f"T_MSG: Error al abrir puerto serial: {e}")
            return


    ser.reset_input_buffer()
    ser.flushInput()
    print("T_MSG: Intentando conectar...")

    success = False

    ser.write(b'CHCON\n') # Comando para establecer conexión 'CHCON\n'

    # Se lee el puerto serial 3 veces. El tercer mensaje es el de conexión exitosa.
    # 1. La primera lectura corresponde al ACK que es el retorno del comando.
    # 2. La segunda lectura es un espacio en blanco (hay que verificar)
    # 3. La tercera lectura es el string 'CONOK\n'
    for i in range(3):
        
        # Espera de 1 seg
        ser.timeout = 1 
        recibe = ser.readline().decode('utf-8', errors='ignore')
        print(f'T_MSG: lectura n. {i+1}')
        print(f'S_MSG: {recibe}')
        
        if "CONOK" in recibe: # Se verifica string de conexión exitosa enviado por el ESP32 ('CONOK\n')
            success = True
            break
    
    if success:
        # Se indica por la terminal que se logró la conexión
        print("T_MSG: Conectado")
        # Se indica el estado de conexión en el GUI
        botCon.configure(bg="red", fg="white") 
        labConStatus.config(text="Conectado", fg="green")
        botCon.config(state="disabled")
        # Se habilitan los botones de control para el sensor
        botLdon.config(state="normal")
        botLason.config(state="normal")
        botonDE.config(state="normal")
        botonSaveSpec.config(state="normal") 
        botonSaveIm.config(state="normal") 
        botVbat.config(state="normal")
        botATI.config(state="normal")
        
        # Config. inicial para ajustar tiempo de integración y medir por primera vez la bateria.
        ajutint()
        monitoreo_automatico_vbat()

    else:
        print("T_MSG: No se recibió respuesta del sensor")
        # Se indica fallo de conexión
        labConStatus.config(text="Fallo Conexión", fg="orange")
        ser.close()

# Función para ajuste de tiempo de integración
def ajutint():
    """
    Ajuste de tiempo de integración del espectrometro de acuerdo al textbox del GUI.
    """
    ser.flushInput()
    # se toma el valor de tiempo de int. en la interfaz y se arma mensaje
    vti = tbati.get('1.0', tk.END)
    vtid3 = int(int(vti))
    strparati = "AjHTI" + str(vtid3) + "\n"
    bobj = bytes(strparati, 'utf-8')
    # se envia mensaje al ESP32 y se muestra en la terminal
    ser.write(bobj)
    print('T_MSG:',strparati)
    # Se lee la confirmación del ESP32
    recibe = ser.readline().decode('utf-8', errors='ignore') # Este primer string creo que es un espacio en blanco
    recibe = ser.readline().decode('utf-8', errors='ignore') # Este string es la confirmacio2n del comando 'AjHTI'+Tint+'\n'
    print('S_MSG:',recibe)
    # Se guarda el dato de tiempo de integración
    global EstTint
    EstTint = int(vti)

#  Función que ejecuta la función de medición despues de 15 segundos
def MedDE():
    """
    Inicia temporizador antes de hacer medición. Esto automatiza la toma de mediciones
    para evitar hacer conteo manual de los 15 segundos.
    """
    global medicion_en_progreso
    medicion_en_progreso = True # Se bloquea el puerto para otras funciones

    print("T_MSG: Inicia retraso de 15 seg. antes de comenzar la medición...")
    # Deshabilita el botón "Medir D/E" para evitar clics múltiples
    botonDE.config(state="disabled")

    # Programa la ejecución de _MedDE_execute después de 15000 ms (15 seg)
    root.after(15000, _MedDE_execute)

# Función para realizar mediciones. Llama graficas y guardado de datos
def _MedDE_execute():
    """
    Envío de comando SCAN para medición. Se lee la respuesta del sensor.
    La respuesta se lee en 5 readline()
    """
    global DisResults, EmiResults, medicion_en_progreso
    
    try:
        ser.reset_input_buffer()
        ser.write(b'SCAN\n')

        # Espera para realizar la captura 
        ser.timeout = 5  
        
        # Los datos se leen en el siguiente orden:
        # 1. ACK
        # 2. Dispersion Data
        # 3. Emission Data
        # 4. Vbat
        # 5. Prediction (ppm)

        # Se verifica confirmación del comando de medición (SCAN)
        recibe_d = ser.readline()
        if recibe_d == b'SCAN\n':
            print("T_MSG: Medición en curso...")

        # Dispersion
        recibe_d = ser.readline()
        DisResults = parse_serial_data(recibe_d, expected_length=50)

        # Emision
        recibe_e = ser.readline()
        EmiResults = parse_serial_data(recibe_e, expected_length=50)
        
        # Voltaje
        recibe_vbat = ser.readline()
        volt_str = recibe_vbat.decode('utf-8', errors='ignore').strip()

        if volt_str: 
            try:
                global EstVolt
                EstVolt = float(volt_str)
                if EstVolt < 7.3:
                    bat_color = 'red'
                else:
                    bat_color = 'green'
                labVbat.config(text=f"{EstVolt:.2f} V", fg=bat_color)
            except ValueError:
                 labVbat.config(text="Err", fg="orange")
        else:
            labVbat.config(text="---") 
        print(f"S_MSG: voltaje, {recibe_vbat}")

        # Predicción
        recibe_ppm = ser.readline()
        print(f"S_MSG: predicción, {recibe_ppm}")

        ser.timeout = 1
        # Se grafican los resultados de la medición 
        grafDE(DisResults, EmiResults)
        guardado()
        
    except Exception as e:
        print(f"T_MSG: Error, {e}")
    finally:
        botonDE.config(state="normal")
        medicion_en_progreso = False # Liberamos el puerto

# Función para graficar curvas de dispersión y emisión despues de una medición
def grafDE(valoresD, valoresE):
    """
    Genera las graficas para visualizar en el GUI.
    """
    global current_canvas_widget

    # Se limpian figuras previas para reducir uso de memoria
    plt.close('all') 
    if current_canvas_widget is not None:
        current_canvas_widget.destroy()

    # Tablas de longitudes de onda y etiquetas
    longs = np.linspace(340, 850, 50) 
    colorbars = np.array([wavelength_to_rgb(w) for w in longs])

    # Se crea una figura con dos subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1 dispersión
    if len(valoresD) == 50: 
        #valoresD = parse_serial_data(str(valoresD).encode(), 50)
        intmaxsenD = valoresD.max()
        ax1.scatter(longs, valoresD, color=colorbars, s=20)
        ax1.set_ylabel('Intensidad')
        ax1.set_xlabel('Longitud de onda [nm]')
        ax1.set_title('Espectro de Dispersión')
        ax1.set_ylim(0, intmaxsenD * 1.2 if intmaxsenD > 0 else 10)
        ax1.tick_params(axis='both', which='major', labelsize=8)

    # Plot 2 Emisión
    if len(valoresE) == 50: 
        #valoresE = parse_serial_data(str(valoresE).encode(), 50)
        intmaxsenE = valoresE.max()
        ax2.scatter(longs, valoresE, color=colorbars, s=20)
        ax2.set_xlabel('Longitud de onda [nm]')
        ax2.set_title('Espectro de Emisión')
        ax2.set_ylim(0, intmaxsenE * 1.2 if intmaxsenE > 0 else 10)
        ax2.tick_params(axis='both', which='major', labelsize=8)

    plt.tight_layout() 

    canvas = FigureCanvasTkAgg(fig, master=root)
    current_canvas_widget = canvas.get_tk_widget() # Save reference
    current_canvas_widget.place(x=0, y=40)
    canvas.draw()

# Función para guardar datos (Parece que esta es redundante, incluir en GuardaDatos())
def guardado():
    """
    Función que llama la rutina de guardado de los datos de una medición
    """
    nombremed = tbNombre.get("1.0", "end-1c")
    concmed = tbConc.get("1.0", "end-1c")

    datosMed = [nombremed, concmed, "---"]
    datosMed.extend(DisResults)
    datosMed.extend("-")
    datosMed.extend(EmiResults)

    GuardaDato(datosMed)

    # Se rehabilita el botón cuando la medición termina.
    print("'T_MSG: Medición finalizada.")
    botonDE.config(state="normal")

# Funcion para guardar datos de las mediciones
def GuardaDato(datos):
    """
    Se guardan los datos obtenidos de la medición en un archivo csv.
    """
    # Ruta del archivo
    file_path = '/Users/andresmr/Documents/Glyphosate_sensor_CFATA/samples/datosDisEmi.csv'
    file_exists = False
    try:
        with open(file_path, 'r') as file:
            file_exists = True
    except FileNotFoundError:
        pass

    # Se abre el archivo y se agregan los datos
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(datos)

# función para medir voltaje de batería
def midvbat():
    """Envío de comando para lectura de voltaje de bateria. También obtiene respueta del sensor y muestra el valor."""
    if not ser.is_open:
        labVbat.config(text="N/C") 
        return
    try:
        # Se limpia el buffer
        ser.reset_input_buffer()
        ser.flushInput()
        # Se manda comando de voltaje
        ser.write(b'MBAT\n')

        recibe_val = ser.readline() # Este string es la confirmación del ESP32 (MBAT)
        recibe_val = ser.readline() # Este string debería ser un espacio en blanco (falta revisar)
        recibe_val = ser.readline() # Este string es el voltaje de la bateria.

        if not recibe_val:
            print("T_MSG: TimeOut en midvbat - El sensor no respondió.")
            labVbat.config(text="T/O", fg="orange") # Timeout
            return
        
        # Se indica el último string que se recibió
        print(f"S_MSG: voltaje, {recibe_val}")
        # Se decodifica el voltaje en el mensaje recibido del ESP32
        volt_str = recibe_val.decode('utf-8', errors='ignore').strip()
        if volt_str: 
            try:
                global EstVolt
                EstVolt = float(volt_str)
                if EstVolt < 7.3:
                    bat_color = 'red'
                else:
                    bat_color = 'green'
                labVbat.config(text=f"{EstVolt:.2f} V", fg=bat_color)
            except ValueError:
                 labVbat.config(text="Err", fg="orange")
        else:
            labVbat.config(text="---") 
    except Exception as e:
        print(f"T_MSG: Error al medir voltaje, {e}")
        labVbat.config(text="Err")

# Funcion para checado de voltaje recurrente
def monitoreo_automatico_vbat():
    """Ejecuta midvbat() cada 15 segundos si el puerto está libre."""
    global medicion_en_progreso
    
    # Solo si está conectado y NO hay una medición SCAN o ajuste en curso
    if ser.is_open and not medicion_en_progreso:
        print("T_MSG: Ejecutando monitoreo automático de batería...")
        midvbat()
    
    # Se programa a sí misma para dentro de 15 segundos
    # Puedes ajustar el tiempo aquí
    root.after(15000, monitoreo_automatico_vbat)

# Funciones para encender y apagar el LED
def DisLedOn():
    ser.flushInput()
    # Envío de comando para encender el LED
    ser.write(b'DISLEDON\n')
    recibe = ser.readline()
    #print('S_MSG:',recibe)
    labLEDStatus.config(text="ON", fg="green")
    botLdon.config(state="disabled")
    botLdoff.config(state="normal")

def DisLedOff():
    ser.flushInput()
    # Envío de comando para apagar el LED
    ser.write(b'DISLEDOFF\n')
    recibe = ser.readline()
    #print('S_MSG:',recibe)
    labLEDStatus.config(text="OFF", fg="red")
    botLdoff.config(state="disabled")
    botLdon.config(state="normal")

# Funciones para encender y apagar el laser (a 750mA)
def LasOn():
    ser.flushInput()
    # Envío de comando para encender el laser
    ser.write(b'LasOn\n')
    recibe = ser.readline()
    #print('S_MSG:',recibe)
    labLaserStatus.config(text="ON", fg="green")
    botLason.config(state="disabled")
    botLasoff.config(state="normal")

def LasOff():
    ser.flushInput()
    # Envío de comando para apagar el laser
    ser.write(b'LasOff\n')
    recibe = ser.readline()
    #print('S_MSG:',recibe)
    labLaserStatus.config(text="OFF", fg="red")
    botLasoff.config(state="disabled")
    botLason.config(state="normal")

# Función para cerrar el puerto y el programa
def alcerrar():
    ser.close()
    # Pone parametros en default
    root.destroy()

# Revisar esta función 
def med_espect(esopt):
    # Se crea lista con longitudes desde 340 a 850
    longs = np.linspace(340, 850, 50)    
    bar_labels = np.linspace(340, 850, 50)  
    colorbars = np.array([wavelength_to_rgb(w) for w in longs])
   
    # Hace medicion y grafica valores.
    ser.flushInput()

    # Se envía comando de mediciones (10 datos)
    ser.write(b'MVal\n')
    # Se reciben los datos
    recibe = ser.readline()
    print('S_MSG:',recibe)
    recibe = ser.readline()
    input_string = recibe

    # Se decodifican los datos separados por comas
    values_str = input_string.decode('utf-8').split(',')
    values_float = [float(value) for value in values_str if value.strip()]
    result_array = np.array(values_float)

    # Obtiene valor maximo del arreglo de resultados
    intmaxsen = result_array.max()
    intminsen = result_array.min()
   
    # Ajuste de figura
    fig, ax = plt.subplots(figsize=(6, 6))

    if (esopt == 3):
        fig, ax = plt.subplots(figsize=(12, 6)) 

    ax.scatter(longs, result_array, color=colorbars, label=bar_labels)
    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)

    if (esopt == 1):
        ax.set_title('Espectro de Dispersión')
        plt.xticks(fontsize=7)

    if (esopt == 2):
        ax.set_title('Espectro de Emisión')
        plt.xticks(fontsize=7)

    if (esopt == 3):
        ax.set_title('Espectro')  
        plt.xticks(fontsize=10) 

    # Checa si es autolimite o no
    if (cheal_state.get() == True):
        limplotya = int(intmaxsen * 1.2)
        limplotyb = int(intminsen * 0.6)
        if intmaxsen == 0:
            intmaxsen = 1
    
    # Fija el limite del eje y 
    ax.set_ylim(limplotyb, limplotya)

    # Para dibujarlo en la ventana del GUI
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()

    if (esopt == 1):
        canvas_widget.place(x=0, y=40)

    if (esopt == 2):
        canvas_widget.place(x=600, y=40)  

    if (esopt == 3):
        canvas_widget.place(x=0, y=40)   

    print("T_MSG: otro")
    global DisResults
    global EmiResults

    if (esopt == 1):
        DisResults = result_array

    if (esopt == 2):
        EmiResults = result_array

# Esta función aún no se revisa
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

# Revisar esta funcion
def guaIma():
    # Función para guardar datos en una imagen
    inivenx = root.winfo_x()
    iniveny = root.winfo_y() + 75
    finvenx = int(inivenx + 1200)
    finveny = int(iniveny + 600)
    screenshot = ImageGrab.grab(bbox=(inivenx, iniveny, finvenx, finveny))
    # Save the screenshot as an image
    nombrearchivo = tbNombre.get("1.0", "end-1c") + '.png'
    screenshot.save(nombrearchivo)

##################################################################################################

# Diseño grafico del GUI
# Abre ventana, para usarse como GUI
root = tk.Tk()
# Pone el nombre de la ventana
root.title("Control de equipo sensor Glifosato")
# Ajusta el tamaño y lo deja fijo 
root.geometry("1200x800")

# Etiquetas para status de conexión
labConStatic = tk.Label(root, text="Status de conexión: ", fg="black") 
labConStatic.place(x=465, y=8)

labConStatus = tk.Label(root, text="Sin conexión", fg="red")
labConStatus.place(x=590, y=8) # 'x' está ajustado para que aparezca después de la etiqueta 1

# Botones de Conexion, mediciones y guardado
botCon = tk.Button(root, text="Conectar", command=conectar)
botCon.place(x=700, y=5)

# Boton para hacer medicion de dispersion, 
botonDE = tk.Button(root, text="Medir D/E", command=MedDE)
botonDE.place(x=20, y=650)
botonDE.config(state="disable")

# Boton para guardar emisión, 
botonSaveSpec = tk.Button(root, text="Espectro", command=lambda: med_espect(3))
botonSaveSpec.place(x=120, y=650)
botonSaveSpec.config(state="disable")

# Boton para guardar imagen de espectroscopia, 
botonSaveIm = tk.Button(root, text="Guardar Imagen", command=guaIma)
botonSaveIm.place(x=220, y=650)
botonSaveIm.config(state="disable")

# Caja para el tiempo de integracion
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

# Cajas para meter datos de medicion
# Nombre de la medicion
labNombre = tk.Label(root, text="Nombre Medición")
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

# Ajuste de limites de graficacion en y
cheal_state = tk.IntVar(value=1)
cheal = tk.Checkbutton(root, text="Auto ajuste Y", variable=cheal_state)
cheal.place(x=700, y=700)

tblim = tk.Text(root, height=1, width=6)
tblim.insert(tk.END, "300")
tblim.place(x=800, y=700)

# Boton para medir batería
pos_x_boton = 960
separacion_boton_etiqueta = 110

botVbat = tk.Button(root, text="Medir", command=midvbat)
botVbat.place(x=pos_x_boton+50, y=658)
botVbat.config(state="disabled") 

labVbat = tk.Label(root, text="Nivel de batería:")
labVbat.place(x=pos_x_boton, y=630+10)

labVbat = tk.Label(root, text="-----")
labVbat.place(x=pos_x_boton, y=663)

# Botones para control del LED
labLED = tk.Label(root, text="Control del LED:")
labLED.place(x=450, y=630+10)
labLEDStatus = tk.Label(root, text="OFF", fg='red')
labLEDStatus.place(x=560, y=630+10)

botLdon = tk.Button(root, text="LED On", command=DisLedOn)
botLdon.place(x=450, y=650+10)

botLdoff = tk.Button(root, text="LED Off", command=DisLedOff)
botLdoff.place(x=530, y=650+10)
botLdoff.config(state="disabled")
botLdon.config(state="disabled")

# Botones para control del laser
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

# Desplienga en la GUI logos: UNAM, CFATA Y CONACYT
# Carga las imagenes
orimage1 = Image.open("LogoCFATA.png")  
width, height = 120, 60
image1 = orimage1.resize((width, height))
photo1 = ImageTk.PhotoImage(image1)
portalogo1 = tk.Label(root, image=photo1)
portalogo1.place(x=900, y=800-80)

orimage2 = Image.open("secihti_logo.jpg")  
width, height = 150, 60 
image2 = orimage2.resize((width, height))
photo2 = ImageTk.PhotoImage(image2)
portalogo2 = tk.Label(root, image=photo2)
portalogo2.place(x=900+125, y=800-80)

# Cuando se cierra la ventana se corre una rutina
root.protocol("WM_DELETE_WINDOW", alcerrar)
root.mainloop()