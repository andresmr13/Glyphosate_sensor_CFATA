
# Programa Control V6,
# Programa para tomar datos de entrenamiento de redesd neuronales
# Se integra proceso de medicion de luz dispersada y luz emitida.
#Se homologa para que sea exactamente la misma metodologia para medir datos de entrenamiento y medicion molecular
# Elaborado por Alejandro Gimenez, 20 Julio 2024
#Esta version recibe datos seleccionados (100) para tener mejor resolucion y tener una red neuronal de tamañol viable para ESP32.


#Importa dependencias

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

#Declaraciones globales

ser = serial.Serial()
ser.baudrate = 115200
#ser.port = 'COM3' #Cambiar dependiendo del puerto usado 
ser.port = '/dev/cu.usbserial-0001' # Este es el puerto en mi mac @Andres.                         

#Esta variable nos dice si esta conectado o no
conectado=False

#Limite de grafica en intensidad
limploty=300

#Variables para guardar los valores de Tint, Gan y Temp
EstTint=700
EstGan=16
EstTemp=20.00
EstVolt=7.2           

#Arreglo de datos Dispersion
DisResults=np.zeros(288, dtype=int)
#DisResults=np.array([0])
EmiResults=np.zeros(288, dtype=int)

#Funcion para guardar datos de las mediciones

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


#///////////////////////////////////////////////////////////////////////////////////////////////////////////////

def conectar():
#Inicio de comunicacion////////////////////////////////////////////////////////////////////////////////////////////////////
    print(ser)
    print(ser.is_open)

    if (ser.is_open==False):
        ser.open()

    #ser.flushInput()

    recibe=""
    while (recibe!=b'CONOK\r\n'):

        ser.flushInput()
        ser.write(b'CHCON\n')
        recibe=ser.readline()
        print(recibe)
        recibe=ser.readline()
        print(recibe)

    print("conectado")
    #current_color = botCon.cget("bg")
    #new_color = "red" if current_color == "blue" else "blue"
    botCon.configure(bg="red")

    #Configura alto tiempo de integracion y ganancia
    ajutint()



#Ajuste de tiempo de integracion////////////////////////////////////////////////////////////////////////////////////
    
def ajutint():
    ser.flushInput()

    #strparaati="AjTiIn"
    
    vti=tbati.get('1.0',tk.END)

    vtid3=int(int(vti))

    strparati="AjHTI" + str(vtid3) + "\n"

    bobj = bytes(strparati, 'utf-8')

    ser.write(bobj)

    #recibe=ser.readline()
    print(strparati)

    #Para guardar dato de tiempo de integracion
    global EstTint
    EstTint=int(vti)





#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////    

        

def med_espect(esopt):


    #Crea lista con longitudes desde 340 a 850

    longs=np.linspace(340, 850, 50)    #288

    bar_labels=np.linspace(340,850,50)  #288

    colorbars=np.array([wavelength_to_rgb(w) for w in longs])
   

    #Hace medicion y grafica valores.

    ser.flushInput()
    #ser.write(b'MVAL\n')      #Medicion de uno solo
    ser.write(b'MVal\n')      #Medicion de 10 datos, antes era MVX10

    recibe=ser.readline()
    print(recibe)
    recibe=ser.readline()

    input_string = recibe

    # Decode the bytes to a string and split it by commas
    values_str = input_string.decode('utf-8').split(',')
    # Convert the string values to floating-point numbers
    values_float = [float(value) for value in values_str if value.strip()]
    # Convert the list to a numpy array
    result_array = np.array(values_float)

    #Obtiene valor maximo del array de resultados
    intmaxsen=result_array.max()
    intminsen=result_array.min()
   

    # Increase the width of the figure
    fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6

    if (esopt==3):
        fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the width (12 inches in this example)    #12,6

    ax.scatter(longs, result_array, color=colorbars, label=bar_labels)

    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)

    if (esopt==1):
        ax.set_title('Espectro Dispersion')
        plt.xticks(fontsize=7)

    if (esopt==2):
        ax.set_title('Espectro Emision')
        plt.xticks(fontsize=7)

    if (esopt==3):
        ax.set_title('Espectro')  
        plt.xticks(fontsize=10) 

    limploty=int(tblim.get('1.0',tk.END))
    #Checa si es autolimite o no
    if (cheal_state.get()==True):
        limplotya=int(intmaxsen*1.2)
        limplotyb=int(intminsen*0.6)
        if intmaxsen==0:
            intmaxsen=1
    #Fija el limite de y 
    
    ax.set_ylim(limplotyb, limplotya)

    #Para dibujarlo en la ventana del GUI
    # Embed the Matplotlib plot in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    #canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    if (esopt==1):
        canvas_widget.place(x=0,y=40)

    if (esopt==2):
        canvas_widget.place(x=600,y=40)  

    if (esopt==3):
        canvas_widget.place(x=0,y=40)   

    
    #root.plt.show()
    
    print("otro")
    global DisResults
    global EmiResults

    if (esopt==1):
        DisResults=result_array

    if (esopt==2):
        EmiResults=result_array

#//////////////////////////////////////////////////////////////////////////////////////////////////
#Hace las dos graficas de una vez
        
def grafDE(valoresD,valoresE):

    #Tablas de longitudes de onda y etiquetas

    longs=np.linspace(340, 850, 50)    #288

    bar_labels=np.linspace(340,850,50)   #288

    colorbars=np.array([wavelength_to_rgb(w) for w in longs])

    #grafica valores.
    #Hace un numpy array de los datos de dispersion
    values_float = valoresD
    result_arrayD = np.array(values_float)

    #Obtiene valor maximo del array de resultados
    intmaxsen=result_arrayD.max()
    intminsen=result_arrayD.min()

    # Increase the width of the figure
    fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6


    ax.scatter(longs, result_arrayD, color=colorbars, label=bar_labels)

    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)

    ax.set_title('Espectro Dispersion')
    plt.xticks(fontsize=7)

    
    limplotyb=int(intmaxsen*1.2)
    limplotya=0                                      #int(intminsen*0.6)
    
    ax.set_ylim(limplotya, limplotyb)

    #Para dibujarlo en la ventana del GUI
    # Embed the Matplotlib plot in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    #canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    canvas_widget.place(x=0,y=40)       #Para dispersion poner en 600,40




    #Hace un numpy array de los datos de emision
    values_float = valoresE
    result_arrayE = np.array(values_float)

    #Obtiene valor maximo del array de resultados
    intmaxsen=result_arrayE.max()

    # Increase the width of the figure
    fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6


    ax.scatter(longs, result_arrayE, color=colorbars, label=bar_labels)

    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=7)

    ax.set_title('Espectro Emision')
    plt.xticks(fontsize=7)

    
    limplotyb=int(intmaxsen*1.2)
    limplotya=0                                #int(intminsen*0.6)
    
    ax.set_ylim(limplotya, limplotyb)

    #Para dibujarlo en la ventana del GUI
    # Embed the Matplotlib plot in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    #canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    canvas_widget.place(x=600,y=40)       #Para dispersion poner en 600,40

   
    #root.plt.show()
    



#/////////////////////////////////////////////////////////////////////////////////////////////////
#//// GUARDA IMAGEN DE ESPECTROSCOPIA
        
def guaIma():

    inivenx=root.winfo_x()
    iniveny=root.winfo_y()+75
    finvenx=int(inivenx+1200)
    finveny=int(iniveny+600)
    screenshot = ImageGrab.grab(bbox=(inivenx, iniveny, finvenx, finveny))
    # Save the screenshot as an image
    nombrearchivo= tbNombre.get("1.0", "end-1c") + '.png'
    screenshot.save(nombrearchivo)


    
#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def guardado():


    nombremed=tbNombre.get("1.0", "end-1c")
    concmed=tbConc.get("1.0", "end-1c")

    #datosMed=[
    #    ['Nombre', 'Concetracion(unids)', 'Dispersion','410nm', '435nm', '460nm', '485nm', '510nm', '535nm', '560nm', '585nm', '610nm', '645nm', '680nm', '705nm', '730nm', '760nm', '810nm', '860nm', '900nm', '940nm', 'Emision','410nm', '435nm', '460nm', '485nm', '510nm', '535nm', '560nm', '585nm', '610nm', '645nm', '680nm', '705nm', '730nm', '760nm', '810nm', '860nm', '900nm', '940nm','Temperatura', 'Voltaje','Tiempo', 'Tintegracion','Ganancia'],
    #    [nombremed, concmed, "---",DisResults[0],DisResults[1],DisResults[2],DisResults[3],DisResults[4],DisResults[5],DisResults[6],DisResults[7],DisResults[8],DisResults[9],DisResults[10],DisResults[11],DisResults[12],DisResults[13],DisResults[14],DisResults[15],DisResults[16],DisResults[17],"---", EmiResults[0],EmiResults[1],EmiResults[2],EmiResults[3],EmiResults[4],EmiResults[5],EmiResults[6],EmiResults[7],EmiResults[8],EmiResults[9],EmiResults[10],EmiResults[11],EmiResults[12],EmiResults[13],EmiResults[14],EmiResults[15],EmiResults[16],EmiResults[17], EstTemp, EstVolt, momento, EstTint,EstGan],
    #]

    datosMed=[nombremed,concmed, "---"]
    datosMed.extend(DisResults)
    datosMed.extend("-")
    datosMed.extend(EmiResults)

    print(datosMed)
    GuardaDato(datosMed)


#////////////////////////////////////////////////////////////////////////////////////////////////////////////
#/// CICLO DE MEDICION DISPERSION Y EMISION
#/////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
def MedDE():

    global DisResults
    global EmiResults

    #Manda comando para medir Glifosato
    ser.flushInput()
    ser.write(b'SCAN\n')

    #Primera linea es el acknoledge
    recibe=ser.readline()
    print(recibe)

  
    #La segunda linea son los valores de dispersion
    recibe=ser.readline()
    input_string = recibe

    # Decode the bytes to a string and split it by commas
    values_str = input_string.decode('utf-8').split(',')
    # Convert the string values to floating-point numbers
    values_float = [float(value) for value in values_str if value.strip()]
    # Convert the list to a numpy array
    result_array = np.array(values_float)

    DisResults=result_array
    mediD=result_array

    #La tercera linea son los valores de emision
    recibe=ser.readline()
    input_string = recibe

    # Decode the bytes to a string and split it by commas
    values_str = input_string.decode('utf-8').split(',')
    # Convert the string values to floating-point numbers
    values_float = [float(value) for value in values_str if value.strip()]
    # Convert the list to a numpy array
    result_array = np.array(values_float)
    EmiResults=result_array
    mediE=result_array


    #Grafica datos
    grafDE(mediD,mediE)

    

    #Guarda datos
    guardado()

    #Recibe resultado de medicion en instrumento
    recibe=ser.readline()
    print(recibe)
    recibe=ser.readline()
    print(recibe)
    #recibe=ser.readline()
    #print(recibe)


#//////////////////////////////////////////////////////////////////////////////////////////////////////////// 
def midvbat():
    ser.flushInput()
    ser.write(b'MBAT\n')

    recibe=ser.readline()
    print(recibe)
    recibe=ser.readline()
    print(recibe)

    labVbat.config(text=recibe)
    global EstVolt
    EstVolt=float(recibe)
    print(EstVolt)

#//// PRENDE Y APAGA LUZ DIFUSA
#////////////////////////////////////////////////////////////////////////////////////////////////////////////   
def DisLedOn():

    ser.flushInput()
    ser.write(b'DISLEDON\n')
    recibe=ser.readline()
    print(recibe)

def DisLedOff():

    ser.flushInput()
    ser.write(b'DISLEDOFF\n')
    recibe=ser.readline()
    print(recibe)


#//// PRENDE Y APAGA LASER (750mA)
#////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
def LasOn():

    ser.flushInput()
    ser.write(b'LasOn\n')
    recibe=ser.readline()
    print(recibe)

def LasOff():

    ser.flushInput()
    ser.write(b'LasOff\n')
    recibe=ser.readline()
    print(recibe)

  


#////////////////////////////////////////////////////////////////////////////////////////////////////////////
def alcerrar():
    ser.close()
    #Pone parametros en default
    
    root.destroy()


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
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

    #return (R, G, B)
    return (R / 255, G / 255, B / 255)  # Normalize RGB values to [0, 1]




    


    

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///  Diseño grafico del GUI
#Ventana principal/////////////////////////////////////////////////////////////////////////////////////////////
#Abre ventana, para usarse como GUI
root=tk.Tk()

#Pone el nombre de la ventana
root.title("Control de equipo sensor Glifosato")


# Ajusta el tamaño y lo deja fijo 
root.geometry("1200x900")
# set minimum window size value
root.minsize(1200, 900)
# set maximum window size value
root.maxsize(1200, 900)
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////


#Botones de Conexion, mediciones y guardado
#Declara boton
botCon=tk.Button(root, text="Conectar", command=conectar)
botCon.place(x=580,y=10)

#Boton de hacer medicion dispersion, 
#boton=tk.Button(root, text="Medir DE", command=lambda: med_espect(1))
boton=tk.Button(root, text="Medir D/E", command=MedDE)
boton.place(x=20,y=650)

#Boton de guardar emision, 
boton=tk.Button(root, text="Espectro", command=lambda: med_espect(3))
boton.place(x=120,y=650)

#Boton para guardar imagen de espectroscopia, 
boton=tk.Button(root, text="Guardar Imagen", command=guaIma)
boton.place(x=220,y=650)



#Ajuste de tiempo de integracion

tbati=tk.Text(root,height=1, width=6)
tbati.insert(tk.END, "50")
tbati.place(x=780,y=665)

#Ajuste de tiempo de integracion
botATI=tk.Button(root, text="Ajuste Tint", command=ajutint)
botATI.place(x=700,y=660)

#Etiqueta de rango de valores permitidos
labati=tk.Label(root, text="1-250 mS")
labati.place(x=780,y=640)


#//////////////////////////////////////////////////////////////////////////////////////////////////////////


#Ventanas para meter datos de medicion

#Nombre de la medicion
labNombre=tk.Label(root, text="Nombre Medicion")
labNombre.place(x=20,y=720)
tbNombre=tk.Text(root, height=1, width=14)
tbNombre.place(x=20,y=740)
tbNombre.insert(tk.END, "Nombre")

#Concentracion molecular
labConc=tk.Label(root, text="Concentracion [ppm]")
labConc.place(x=170,y=720)
tbConc=tk.Text(root, height=1, width=8)
tbConc.place(x=170,y=740)
tbConc.insert(tk.END, "0.0")


#///////////////////////////////////////////////////////////////////////////////////////////////////////////

#Ajuste de limites? de graficacion en y

cheal_state=tk.IntVar(value=1)
cheal= tk.Checkbutton(root, text="Auto ajuste Y", variable=cheal_state)

cheal.place(x=700,y=840)

tblim=tk.Text(root,height=1, width=6)
tblim.insert(tk.END, "300")
tblim.place(x=800,y=845)



#////////////////////////////////////////////////////////////////////////////////////////////////////////////

#Mide Bateria

botVbat=tk.Button(root, text="Bateria", command=midvbat)
botVbat.place(x=1050, y=830)
labVbat=tk.Label(root, text="-----")
labVbat.place(x=1110,y=830)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////

#PRENDE/APAGA LUZ DIFUSA

botLdon=tk.Button(root, text="LED On", command=DisLedOn)
botLdon.place(x=450, y=650)

botLdoff=tk.Button(root, text="LED Off", command=DisLedOff)
botLdoff.place(x=500, y=650)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////

#PRENDE/APAGA LASER

botLason=tk.Button(root, text="Laser On", command=LasOn)
botLason.place(x=450, y=700)

botLasoff=tk.Button(root, text="Laser Off", command=LasOff)
botLasoff.place(x=500, y=700)


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////

#Desplienga en la GUI logos: UNAM, CFATA Y CONACYT
# Carga las imagenes
orimage1 = Image.open("LogoCFATA.png")  
width, height = 200, 100  # Set the desired width and height for the resized image
image1 = orimage1.resize((width, height))
photo1 = ImageTk.PhotoImage(image1)
portalogo1 = tk.Label(root, image=photo1)
portalogo1.place(x=250,y=780)

orimage2 = Image.open("Secihti_logo.png")  
width, height = 100, 100  # Set the desired width and height for the resized image
image2 = orimage2.resize((width, height))
photo2 = ImageTk.PhotoImage(image2)
portalogo2 = tk.Label(root, image=photo2)
portalogo2.place(x=470,y=780)



#Pone en pantalla relacion de intensidades

#labRatio=tk.Label(root,text="560/645")
#labRatio.place(x=460,y=830)


#Cuando se cierra la ventana se corre una rutina
root.protocol("WM_DELETE_WINDOW", alcerrar)


root.mainloop()







