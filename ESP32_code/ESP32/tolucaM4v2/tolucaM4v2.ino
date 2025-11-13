/*
  Programa para microcontrolador ESP32,
  Implementacion para medicion espectral usando sensor Hammamatsu
  Version inicial creada: 19 Marzo 2024
  Version actual: 22 Julio 2024 
  Esta version recorta a 50 longitudes de onda especificamente seleccionadas.
  Se calcula ratio entre los dos picos de emision, la red neuronal solo usa valores de dispersion
  Board: ESP32 DEVMODULE, Particion Scheme: Huge APP
  */

  /* 
  Notas adicionales
  
  Corre con esp32 by Espressif Systems v=2.017 y con EloquentTinyML by Simone v=2.4.4

  Andres Montes de Oca Rebolledo
  */

#include <WiFi.h>         //para deshabilitar el wifi

#include "glifoNN1.h"     //Red neuronal
#include "spectrometer.h"   //Rutina de lectura de espectro


//********************************************************************************************************
// Agrega declaraciones para uso de Bluetooth

#include "BluetoothSerial.h"


//#define USE_PIN // Uncomment this to use PIN during pairing. The pin is specified on the line below
const char *pin = "1234"; // Change this to more secure PIN.

String device_name = "MILPA_003";

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

#if !defined(CONFIG_BT_SPP_ENABLED)
#error Serial Bluetooth not available or not enabled. It is only available for the ESP32 chip.
#endif

BluetoothSerial SerialBT;

//**********************************************************************************************************

float input[100];     

float acur1;
float acur2;
float ratio;

//*****************************************************************

//Define pines de entrada salida

int CuuS;


int Led=2;  //led de la tarjeta incluido
int led_state = LOW;    // estado actual del led
int LedExt=17;  //Led de indicacion, fuera de la caja
int LedDis=22;  //Led para dispersion de luz blanca    //ANTES18
int AnaIn=26;   //Entrada analogica para medir carga de bateria

//Para control del espectrofotometro Hamamatsu




//Configuracion de reloj para medicion y ajuste de corriente del Laser
const byte ledPin = 23;                                                       //Original 33
const uint32_t freq = 10000; // 10 khz, confirmado en osciloscopio
const uint8_t ledChannel = 0;       //original 0
const uint8_t resolution = 2;

//MedSim
float medsim=782.44;
//int simco=1;

//Declara variables a usar
String InData;    //Entrada de datos seriales
int detMensa;     //bandera de deteccion de comandos
String Config;    //Recibe strings para configuraciones
//int TiIn;         //Tiempo de integracion
int AjLas=0;        //Ajuste de laser, valor PWM para hacer ajustes
int AjHTI=50;       //Ajuste de tiempo de integracion Hammamatsu.
int AjNUPR=10;      //Ajuste de numero de promedios
int SULI=0;         //Setup de la corriente del laser
int LasI;         //Corriente medida de consumo del Laser
int conpar;       //Contador de parpadeo de Led Externo
float vbat;       //Valor de voltaje de bateria
float porce;        //Avance porcentual


//*************************************************************************************************
//*************************************************************************************************
//INTERRUPCIONES
//Si el laser esta activo, cada 100uS hace un ajuste de regulacion de corriente.

void LaserAdj() { 

  //Para prueba de timing, deberia parpadera cada 2 segundos
  CuuS=CuuS+1;
  if (CuuS>100) {
    CuuS=0;
    led_state= !led_state;
    //digitalWrite(Led, led_state);
    LasI=analogRead(34);
    if(LasI<SULI-5){
    AjLas=AjLas+1;
    ledcWrite(2,AjLas);  
    }
    if(LasI>(SULI+5)){
    AjLas=AjLas-1;
    ledcWrite(2,AjLas); 
    }
    if(SULI==0) {
      AjLas=0;
      ledcWrite(2,AjLas);
    }
  }
}

//***********************************************************************************************
//***********************************************************************************************


void setup()
{

  //inicia com serial
  Serial.begin(115200);

  // Turn off WiFi
  WiFi.mode(WIFI_OFF);
  WiFi.disconnect(true); // Disconnect from any network and free resources
  
  //inicia pines
  pinMode(Led,OUTPUT);
  digitalWrite(Led,LOW);
  pinMode(LedExt,OUTPUT);
  digitalWrite(LedExt,LOW);
  pinMode(LedDis,OUTPUT);
  digitalWrite(LedDis,LOW);
  pinMode(AnaIn,INPUT);

    //Parpadea led azul ESP32
  for (int i = 0; i <= 10; i++) {
    digitalWrite(Led,HIGH);
    digitalWrite(LedExt,HIGH);
    delay(10);
    digitalWrite(Led,LOW);
    digitalWrite(LedExt,LOW);
    delay(30);
      }

    
    //Inicia red neuronal 1
      while (!glifoNN1.begin()) {
        Serial.print("Error in NN initialization: ");
        Serial.println(glifoNN1.getErrorMessage());
      }
    

    digitalWrite(LedExt,LOW);


  //Mensaje inicial
  Serial.println("MILPA-HR 003, ");
  Serial.println("CFATA UNAM, Mayo 2024");
  Serial.println("Elaborado Alejandro J Gimenez");

  //Inicia modulo de medicion de luz, parpadea hasta lograr com.
  
  digitalWrite(Led,LOW);
 
  //****************************************************************************************************************************
  //Esta parte es para configurar el control de corriente del Laser
  
  //Configura interrupcion para regulacion de Laser
  //Esto es para configurar reloj interno, ahora esta a 10 Khz,  tal vez sera mejor bajar velocidad??
  ledcAttachPin(ledPin, ledChannel);
  ledcSetup(ledChannel, freq, resolution);
  ledcWrite(ledChannel, 7); 
  
  //Configura interrupcion para llevar cuenta de mS
  attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);

  //Configura PWM para control del Laser

  // explicar que son estos valores, canal 2, 1000hz, 10 bits.
  ledcSetup(2,1000,10);
  // Conecta la salida del Pin25 al control de laser
  ledcAttachPin(25,2);

  //Por alguna razon parece que era importante hacer esto al final...
  //Inicia com Bluetooth
  SerialBT.begin(device_name); //Bluetooth device name

  //Declaraciones para Lectura de Espectrofotometro 
  pinMode(SPEC_CLK, OUTPUT);
  pinMode(SPEC_ST, OUTPUT);
  digitalWrite(SPEC_CLK, HIGH); // Set SPEC_CLK High
  digitalWrite(SPEC_ST, LOW); // Set SPEC_ST Low


}

void loop()
{

  //Parpadeo LEDS mientras no recibe nada
  conpar=conpar+1;
  if (conpar>800) {
  if (conpar>900) conpar=0;
  digitalWrite(Led,HIGH);
  digitalWrite(LedExt,HIGH); 
  }
  delay(1);
  digitalWrite(Led,LOW);
  digitalWrite(LedExt,LOW);

//****************************************************************************************
//Esta parte del codigo es para seleccionar comunicacion Serial o BT

  //Espera recibir comando Bluetooth o Serial
  if (Serial.available()>0 or SerialBT.available()>0) {     

  if (SerialBT.available()>0) InData=SerialBT.readString();
  if (Serial.available()>0) InData=Serial.readString();
  
  Serial.print(InData);           //Contesta de regreso info recibida como ACK.


  //****Verifica puerto de comunicacion
  //*****************************************************************************************************

  detMensa=InData.indexOf("CHCON");       
  if (detMensa!=-1){
  Serial.println("CONOK");
  }

  //********************************************************************************************************
  //********************************************************************************************************
  //****Hace medicion de contenido de glifosato
  detMensa=InData.indexOf("SCAN");                    //Poner aqui el comando del otro equipo
 
  if (detMensa!=-1){

    //Pone a dormir Bluettoth para no interferir medicion
    //esp_bluedroid_disable();
    //esp_bt_controller_disable();

    

    //Manda string para pantalla bluetooth
    SerialBT.println("En proceso...");
    
    //Prende led de difusion de luz
    digitalWrite(LedDis,HIGH);

    delay(100);
    leeSpec(1,30,0);      //1mS para dispersion, 30 veces, dispersion
    attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);

    //mete datos 0-50 en input

    for (int i=0; i<50; i++){
      input[i]=pdata[i];
    }
    
    //Apaga led de difusion
    digitalWrite(LedDis,LOW);

    //Prende LASER
    //Pone el SetUp en 1200=750mA, 700=400mA
    SULI=700;
    //Adelanta valor inicial para no tardar demasiado en subir corriente
    AjLas=550;
    delay(3000);    //Parece que existe una fluorescencia, esto tiene que ser mayor a 3 segundos
 
    leeSpec(80,1,1);     //80 mS para emision, 1 vez, emision
    attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);


    for (int i=0; i<50; i++){
      input[i+50]=pdata[i];
      }

    
        
    //Apaga LASER
    //Pone el SetUp en 0=0mA
    SULI=0;
    //Adelanta valor inicial para no tardar demasiado en bajar corriente
    AjLas=0;
           
    //Mide bateria
    vbat=analogRead(26);
    vbat=vbat*0.01061;
   
    //Hace inferencia
    float medicion1 = glifoNN1.predict(input);
  
    Serial.println(vbat);
    


    delay(100); 

    //if (medicion1<80){              //Esto no se para que es ;);)
    //  medicion1=medicion1/5;
    //}
    int medentero1=medicion1;
      
    //Manda dato de medicion por bluetooth y Serial
    Serial.print(medentero1);
    Serial.println(" ppm");

    //Conecta de regreso el Bluetooth
    //esp_bt_controller_enable(ESP_BT_MODE_CLASSIC_BT);
    //esp_bluedroid_enable();
    //SerialBT.begin(device_name);
  
    //******************************

    SerialBT.print(medentero1);
    SerialBT.println(" ppm");

      //for (int i=0; i<50; i++){
      //Serial.println(input[i]);
      //}
  }


  //********************************************************************************************************
  //********************************************************************************************************



  //*************************************************************************************************************
  //**** Prende y apaga la luz de dispersion LED blanco

  detMensa=InData.indexOf("DISLEDON");       
  if (detMensa!=-1){
  digitalWrite(LedDis,HIGH);
  }

  detMensa=InData.indexOf("DISLEDOFF");       
  if (detMensa!=-1){
  digitalWrite(LedDis,LOW);
  }


  //*************************************************************************************************************
  //****Mide carga bateria

  detMensa=InData.indexOf("MBAT");       
  if (detMensa!=-1){
 
  vbat=analogRead(26);
  vbat=vbat*0.01061;
  Serial.println(vbat, 2);

  }

  //****Ajusta valor de tiempo de integracion Hammamatsu
  //*************************************************************************************

  detMensa=InData.indexOf("AjHTI");
  if (detMensa!=-1){
  Config=InData.substring(detMensa+5);
  AjHTI= Config.toInt();
  Serial.print("AjHTI=");
  Serial.println(AjHTI); 
  }

  //****Ajusta valor de tiempo de numero de promedios
  //*************************************************************************************

  detMensa=InData.indexOf("AjNUPR");
  if (detMensa!=-1){
  Config=InData.substring(detMensa+6);
  AjNUPR= Config.toInt();
  Serial.print("AjNUPR=");
  Serial.println(AjNUPR); 
  }


  //*************************************************************************************************************
  //*************************************************************************************************************
  //****LASER
  //****Pone valor de PWM
  //*************************************************************************************

  detMensa=InData.indexOf("AjLas");
  if (detMensa!=-1){
  Config=InData.substring(detMensa+5);
  AjLas= Config.toInt();
  Serial.print("AjLas=");
  Serial.println(AjLas); 
  ledcWrite(2,AjLas);
  }

  //****Lee valor de ADC
  //*************************************************************************************

  detMensa=InData.indexOf("MideI");
  if (detMensa!=-1){

  LasI=analogRead(34);
  Serial.print("I=");
  Serial.println(LasI); 
  }

  //****Establece setup de corriente
  //*************************************************************************************

  detMensa=InData.indexOf("SetUp");
  if (detMensa!=-1){
  Config=InData.substring(detMensa+5);
  SULI= Config.toInt();
  Serial.print("Setup Curr=");
  Serial.println(SULI); 
  }

  
  //****Prende Laser
  //*************************************************************************************

  detMensa=InData.indexOf("LasOn");
  if (detMensa!=-1){
  //Pone el SetUp en 1200=750mA
  SULI=700;    //700-aprox 400mA
  //Adelanta valor inicial para no tardar demasiado en subir corriente
  AjLas=550;

  }

  //****Apaga Laser
  //*************************************************************************************

  detMensa=InData.indexOf("LasOff");
  if (detMensa!=-1){
  //Pone el SetUp en 0=0mA
  SULI=0;
  //Adelanta valor inicial para no tardar demasiado en bajar corriente
  AjLas=0;

  }

  //**********************************************************************************************************************

 
  
  //****Hace medicion de valores
  //***************************************************************************************

  //****Hace medicion de valores promediando varias veces...
  //***************************************************************************************
  detMensa=InData.indexOf("MVal");       
  if (detMensa!=-1){

  delay(100);
  leeSpec(AjHTI,AjNUPR,0);         //Manda edicion de dispersion
  attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);
 
 

  }

}
}


//**********************************************************************************************************************************













//*******************************************************************************************************
