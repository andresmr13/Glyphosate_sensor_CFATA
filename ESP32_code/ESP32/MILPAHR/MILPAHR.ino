/*
  Programa para microcontrolador ESP32,
  Implementacion para medicion espectral usando sensor Hammamatsu
  Version actual: 11 Julio 2024 
  Esta version despliega todos los datos medidos por el espectrofotometro 288 canales.
  Board: ESP32 DEVMODULE, Particion Scheme: Huge APP
*/

//#include "glifoNN1.h"     //Red neuronal
//#include "spectrometer.h"   //Rutina de lectura de espectro


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


//Definiciones de la parte del espectrometro
#define SPEC_TRG         19     //23
#define SPEC_ST          33
#define SPEC_CLK         32
#define SPEC_VIDEO       2

#define SPEC_CHANNELS    288 // New Spec Channel
uint16_t data[SPEC_CHANNELS];
float    dataacu[SPEC_CHANNELS];     //Acumulador

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
int simco=1;

//Declara variables a usar
String InData;    //Entrada de datos seriales
int detMensa;     //bandera de deteccion de comandos
String Config;    //Recibe strings para configuraciones
int TiIn;         //Tiempo de integracion
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
    //AjLas=AjLas+1;
    ledcWrite(2,AjLas);  
    }
    if(LasI>(SULI+5)){
    //AjLas=AjLas-1;
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

    /*
    //Inicia red neuronal 1
      while (!glifoNN1.begin()) {
        Serial.print("Error in NN initialization: ");
        Serial.println(glifoNN1.getErrorMessage());
      }
    */

    digitalWrite(LedExt,LOW);


  //Mensaje inicial
  Serial.println("MILPA-HR 003, ");
  Serial.println("CFATA UNAM, Julio 2024");
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

      
    //Prende led de difusion de luz
    digitalWrite(LedDis,HIGH);

    delay(100);
    leeSpec(1);      //1mS para dispersion, 10 veces
    //attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);
    
    //Apaga led de difusion
    digitalWrite(LedDis,LOW);

    //Pone el SetUp en 1200=750mA, 700=400mA
    SULI=700;
    //Adelanta valor inicial para no tardar demasiado en subir corriente
    AjLas=550;
    delay(3000);    //Parece que existe una fluorescencia, esto tiene que ser mayor a 3 segundos
    leeSpec(50);     //50 mS para emision
    //attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);
          
    //Apaga LASER
    //Pone el SetUp en 0=0mA
    SULI=0;
    //Adelanta valor inicial para no tardar demasiado en bajar corriente
    AjLas=0;
           
    //Mide bateria
    vbat=analogRead(26);
    vbat=vbat*0.01061;
   
    //Hace inferencia
    //float medicion1 = glifoNN1.predict(input);
  
    Serial.println(vbat);
    Serial.println("todo");

    delay(100); 

    int medentero1=0;
      
    //Manda dato de medicion por bluetooth y Serial
    Serial.print(medentero1);
    Serial.println(" ppm");

    SerialBT.print(medentero1);
    SerialBT.println(" ppm");
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
  SULI=1200;    //700-aprox 400mA
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
  leeSpec(AjHTI);
 
 

  }

}
}


//**********************************************************************************************************************************

/*
 * This functions reads spectrometer data from SPEC_VIDEO
 * Look at the Timing Chart in the Datasheet for more info
 */
void readSpectrometer(int bande){

  int delayTime = 1; // delay time

  // Start clock cycle and set start pulse to signal start
  digitalWrite(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  digitalWrite(SPEC_ST, HIGH);
  delayMicroseconds(delayTime);

  //Sample for a period of time
  for(int i = 0; i < 15; i++){

      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
 
  }

  //Set SPEC_ST to low
  digitalWrite(SPEC_ST, LOW);

  //Sample for a period of time
  for(int i = 0; i < 85; i++){

      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
      
  }

  //One more clock pulse before the actual read
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);

  //Aqui apaga el PWM para evitar ruidos, apaga ****************************************************
  if (bande==1){
  ledcWrite(2,0);
  detachInterrupt(digitalPinToInterrupt(23)); 
  
  }
  //************************************************************************************************

  //Read from SPEC_VIDEO
  for(int i = 0; i < SPEC_CHANNELS; i++){

      data[i] = analogRead(SPEC_VIDEO);
      
      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime);
        
  }

  //Set SPEC_ST to high
  digitalWrite(SPEC_ST, HIGH);

  //Sample for a small amount of time
  for(int i = 0; i < 7; i++){
    
      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime);
    
  }

  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);

  
  
}





/*
 * The function below prints out data to the terminal or 
 * processing plot
 */
void printData(){

  
  for (int i = 0; i < SPEC_CHANNELS; i++){

    Serial.print(data[i]);
    Serial.print(',');
    
  }

  Serial.println(" ");

  
}


//Aqui esta subrutina sirve para pedir medicion al espectrofotometro
//manda 288 renglones con info de 340 a 850, paso= 1.77nm

void leeSpec(int tiint){

  readSpectrometer(0);
  delay(tiint);
  readSpectrometer(1);
  //prende de nuevo laser
  attachInterrupt(digitalPinToInterrupt(ledPin),LaserAdj, RISING);
  
  //Normaliza linea base
    float vmin=4000;
    
    for (int i = 0; i < SPEC_CHANNELS; i++){
    if (data[i]<vmin){
      vmin=data[i];
    }
    }

    for (int i = 0; i < SPEC_CHANNELS; i++){
    data[i]=data[i]-vmin;
    } 
  
  //Normaliza pico, saca el pico del promedio de los 7 valores mas altos.

    float vmax1=0;
    float vmax2=0;
    float vmax3=0;
    float vmax4=0;
    float vmax5=0;
    float vmax6=0;
    float vmax7=0;
    float vmax8=0;
    float vmax9=0;
    int aqui;

    for (int i = 0; i < SPEC_CHANNELS; i++){
    if (data[i]>vmax5){
      vmax5=data[i];
      aqui=i;
    }
    }
    

    //Suma los 4 valores anteriores y posteriores a vmax4.
    vmax1=data[aqui-4];
    vmax2=data[aqui-3];
    vmax3=data[aqui-2];
    vmax4=data[aqui-1];
    vmax6=data[aqui+1];
    vmax7=data[aqui+2];
    vmax8=data[aqui+3];
    vmax9=data[aqui+4];

    vmax5=vmax1+vmax2+vmax3+vmax4+vmax5+vmax6+vmax7+vmax8+vmax9;
    vmax5=vmax5/9;
    
    for (int i = 0; i < SPEC_CHANNELS; i++){
    data[i]=(1000*(data[i]/vmax5));
    }  
  
  printData();
  
}


//*******************************************************************************************************
