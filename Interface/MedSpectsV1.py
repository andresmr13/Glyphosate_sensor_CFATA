
# Programa Control V5,
# Programa para tomar datos de entrenamiento de redesd neuronales
# Se integra proceso de medicion de luz dispersada y luz emitida.
#Se homologa para que sea exactamente la misma metodologia para medir datos de entrenamiento y medicion molecular
# Elaborado por Alejandro Gimenez, 27 Marzo 2024.
# Nota 15 agosto 2024, esta version sirve para ver todo el espectro y comparar con mediciones de laboratorio 


#Importa dependencias

import serial
import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
from datetime import datetime

from PIL import ImageGrab
from PIL import Image, ImageTk




#Declaraciones globales

ser = serial.Serial()
ser.baudrate = 115200
ser.port = 'COM3'                            #Cambiar dependiendo del puerto usado 

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

vcal=60
color_index = 0
colors = ['black', 'blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']

#limites de ploteo maximos y minimos para todas las graficas.
maxabs=0
minabs=4000



#Funcion para guardar datos de las mediciones

def GuardaDato(datos):

    # Define the file path
    file_path = 'EspectralData.csv'

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


#Ajuste de numero de promedios////////////////////////////////////////////////////////////////////////////////////
    
def ajunupo():
    ser.flushInput()

    #strparaati="AjTiIn"
    
    nupr=tbnupo.get('1.0',tk.END)

    nupr3=int(int(nupr))

    strparanp="AjNUPR" + str(nupr3) + "\n"

    bobj = bytes(strparanp, 'utf-8')

    ser.write(bobj)

    #recibe=ser.readline()
    print(strparanp)

    #Para guardar dato de tiempo de integracion
    global EstNuPr
    EstNuPr=int(nupr)


# ////////////////////////////////////////

def PopPrLD():


    tbati.delete(1.0,tk.END)
    tbati.insert(tk.END, "1")
    tbnupo.delete(1.0,tk.END)
    tbnupo.insert(tk.END, "10")


def PopPrLE():

    tbati.delete(1.0,tk.END)
    tbati.insert(tk.END, "100")
    tbnupo.delete(1.0,tk.END)
    tbnupo.insert(tk.END, "1")

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////    

        

def med_espect(esopt):

    global DisResults
    global EmiResults


    #Crea lista con longitudes desde 340 a 850

    longs=np.linspace(340+vcal, 850+vcal, 288)

    bar_labels=np.linspace(340+vcal,850+vcal,288)

    colorbars=np.array([wavelength_to_rgb(w) for w in longs])
   

    #Hace medicion y grafica valores.

    ser.flushInput()
    #ser.write(b'MVAL\n')      #Medicion de uno solo
    ser.write(b'MVal\n')      #Medicion DE ESPECTRO

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

    DisResults=result_array

    #Obtiene valor maximo del array de resultados
    intmaxsen=result_array.max()
    intminsen=result_array.min()

    #Normaliza si esta el boton

    #global cheno_state

    if (cheno_state.get()==True):
        norm_array = (1000*result_array)/intmaxsen

        #intmaxsen=result_array.max()
        #intminsen=result_array.min()
   

    # Increase the width of the figure
    # fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6


    fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the width (12 inches in this example)    #12,6

    ax.scatter(longs, result_array, color=colorbars, label=bar_labels)

    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=8)

    ax.set_xlabel('Longitud de onda (nm)')
    plt.xticks(fontsize=8)

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
    
    if (esopt==1):
        canvas_widget.place(x=0,y=40)

    if (esopt==2):
        canvas_widget.place(x=600,y=40)  

    if (esopt==3):
        canvas_widget.place(x=0,y=40)   

    
    #root.plt.show()
    
    print("otro")
    

    if (esopt==1):
        DisResults=result_array

    if (esopt==2):
        EmiResults=result_array

    if (esopt==3):
        DisResults=result_array   

    #guarda todos los espectros medidos
    guardado()


def plus_medesp(esopt):

    global color_index
    global maxabs
    global minabs
    global DisResults
    global EmiResults

       #Crea lista con longitudes desde 340 a 850, calibrable

    longs=np.linspace(340+vcal, 850+vcal, 288)

    bar_labels=np.linspace(340+vcal,850+vcal,288)

    colorbars=np.array([wavelength_to_rgb(w) for w in longs])
   

    #Hace medicion y grafica valores.

    ser.flushInput()
    #ser.write(b'MVAL\n')      #Medicion de uno solo
    ser.write(b'MVal\n')      #Medicion DE ESPECTRO

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

    DisResults=result_array

    #Obtiene valor maximo del array de resultados
    intmaxsen=result_array.max()
    intminsen=result_array.min()

    
    if (cheno_state.get()==True):

        #Mormaliza linea base, punto minimo=0.
        #result_array = result_array-intminsen
        #intmaxsen=result_array.max()
        #intminsen=result_array.min()

        #Normaliza pico mas alto
        result_array = (1000*result_array)/intmaxsen
        intmaxsen=result_array.max()
        intminsen=result_array.min()


    intminsen=-100    #Para mejor visualizacion


    if (intmaxsen>maxabs):
        maxabs=intmaxsen

    if (intminsen<minabs):
        minabs=intminsen
   

    # Aqui no declaramos un fig y ax, por eso usa el global

    # fig, ax = plt.subplots(figsize=(6, 6))  # Adjust the width (12 inches in this example)    #12,6
    # fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the width (12 inches in this example)    #12,6


    #ax.scatter(longs, result_array, color=colorbars, label=bar_labels)
    new_color = colors[color_index % len(colors)]
    color_index=color_index+1
    ax.plot(longs, result_array, new_color, label=bar_labels)
    

    ax.set_ylabel('Intensidad')
    plt.yticks(fontsize=8)

    ax.set_xlabel('Longitud de onda (nm)')
    plt.xticks(fontsize=8)

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
        limplotya=int(maxabs*1.2)
        limplotyb=int(minabs*0.6)
        if maxabs==0:
            maxabs=1
    #Fija el limite de y 
    
    ax.set_ylim(limplotyb, limplotya)

    #Para dibujarlo en la ventana del GUI
    # Embed the Matplotlib plot in the Tkinter window

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    
    if (esopt==1):
        canvas_widget.place(x=0,y=40)

    if (esopt==2):
        canvas_widget.place(x=600,y=40)  

    if (esopt==3):
        canvas_widget.place(x=0,y=40)   

    
    #root.plt.show()
    
    print("otro")
    

    if (esopt==1):
        DisResults=result_array

    if (esopt==2):
        EmiResults=result_array

    if (esopt==3):
        DisResults=result_array   

    #guarda todos los espectros medidos
    guardado()
   
    


def borraplo():

    global fig,ax
    global color_index
    global maxabs
    global minabs


    ax.cla()  # Clear the axes
    fig.clf()  # Clear the figure

    color_index=0

    fig,ax = plt.subplots(figsize=(12, 6))  # Adjust the width and height
    # Embed the Matplotlib plot in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()

    maxabs=0
    minabs=4000
    



#/////////////////////////////////////////////////////////////////////////////////////////////////
#//// GUARDA IMAGEN DE ESPECTROSCOPIA
        
def guaIma():

    inivenx=root.winfo_x()+50
    iniveny=root.winfo_y()+75
    finvenx=int(inivenx+1125)    #1200
    finveny=int(iniveny+590)    #600
    screenshot = ImageGrab.grab(bbox=(inivenx, iniveny, finvenx, finveny))
    # Save the screenshot as an image
    nombrearchivo= tbNombre.get("1.0", "end-1c") + '.png'
    screenshot.save(nombrearchivo)


    
#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def guardado():

    momento=datetime.now()
    nombremed=tbNombre.get("1.0", "end-1c")

    datosMed=[nombremed, momento]
    datosMed.extend(DisResults)
    
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
    #grafDE(mediD,mediE)

    #Guarda datos
    guardado()


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

# Create a figure and a set of subplots
fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the width and height
# Embed the Matplotlib plot in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()


#/////////////////////////////////////////////////////////////////////////////////////////////////////////


#Botones de Conexion, mediciones y guardado
#Declara boton
botCon=tk.Button(root, text="Conectar", command=conectar)
botCon.place(x=580,y=10)

#Boton de hacer medicion dispersion, 
#boton=tk.Button(root, text="Medir DE", command=lambda: med_espect(1))
boton=tk.Button(root, text="Medir DE", command=MedDE)
boton.place(x=20,y=650)

#Boton de guardar emision, 
boton=tk.Button(root, text="Espectro", command=lambda: med_espect(3))
boton.place(x=120,y=650)

#Boton para hacer mediciones adicionales
boton=tk.Button(root, text="+Esp", command=lambda: plus_medesp(3))
boton.place(x=120,y=680)

#Boton para borrar mediciones anteriores
boton=tk.Button(root, text="Borra", command=lambda: borraplo())
boton.place(x=160,y=680)

#Boton para guardar imagen de espectroscopia, 
boton=tk.Button(root, text="Guardar Imagen", command=guaIma)
boton.place(x=220,y=650)


#Preajustes para medicion luz difusa y emitida

botPrLD=tk.Button(root, text="Pr LD", command=PopPrLD)
botPrLD.place(x=850,y=660)

botPrLE=tk.Button(root, text="Pr LE", command=PopPrLE)
botPrLE.place(x=850,y=690)


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


#Ajuste de numero de promedios

tbnupo=tk.Text(root,height=1, width=6)
tbnupo.insert(tk.END, "10")
tbnupo.place(x=780,y=690)

#Ajuste de tiempo de integracion
botNUPO=tk.Button(root, text="No Proms", command=ajunupo)
botNUPO.place(x=700,y=690)




#//////////////////////////////////////////////////////////////////////////////////////////////////////////


#Ventanas para meter datos de medicion

#Nombre de la medicion
labNombre=tk.Label(root, text="Nombre Medicion")
labNombre.place(x=20,y=720)
tbNombre=tk.Text(root, height=1, width=14)
tbNombre.place(x=20,y=740)
tbNombre.insert(tk.END, "Nombre")

#Concentracion molecular
labConc=tk.Label(root, text="Concentracion Unidades")
labConc.place(x=170,y=720)
tbConc=tk.Text(root, height=1, width=8)
tbConc.place(x=170,y=740)
tbConc.insert(tk.END, "0.1")


#///////////////////////////////////////////////////////////////////////////////////////////////////////////

#Ajuste de limites? de graficacion en y

cheal_state=tk.IntVar(value=1)
cheal= tk.Checkbutton(root, text="Auto ajuste Y", variable=cheal_state)

cheal.place(x=700,y=840)

tblim=tk.Text(root,height=1, width=6)
tblim.insert(tk.END, "300")
tblim.place(x=800,y=845)

#Opcion de normalizacion

cheno_state=tk.IntVar(value=0)
cheno= tk.Checkbutton(root, text="Normalizacion", variable=cheno_state)

cheno.place(x=700,y=800)

nowl=tk.Text(root,height=1, width=6)
nowl.insert(tk.END, "550")
nowl.place(x=800,y=800)



#////////////////////////////////////////////////////////////////////////////////////////////////////////////

#Mide Bateria

botVbat=tk.Button(root, text="V Bat", command=midvbat)
botVbat.place(x=1050, y=830)
labVbat=tk.Label(root, text="-----")
labVbat.place(x=1110,y=830)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////

#PRENDE/APAGA LUZ DIFUSA

botLdon=tk.Button(root, text="LD On", command=DisLedOn)
botLdon.place(x=450, y=650)

botLdoff=tk.Button(root, text="LD Off", command=DisLedOff)
botLdoff.place(x=500, y=650)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////

#PRENDE/APAGA LASER

botLason=tk.Button(root, text="Las On", command=LasOn)
botLason.place(x=450, y=700)

botLasoff=tk.Button(root, text="Las Off", command=LasOff)
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







