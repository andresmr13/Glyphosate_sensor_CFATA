/*Libreria para tarjeta vieja parchada
 * Macro Definitions
 */
#define SPEC_TRG         19     //23
#define SPEC_ST          33
#define SPEC_CLK         32
#define SPEC_VIDEO       2

#define SPEC_CHANNELS    288 // New Spec Channel
uint16_t data[SPEC_CHANNELS];
float    dataacu[SPEC_CHANNELS];     //Acumulador

#define SALIDAS          50 // reduce numero de canales
uint16_t pdata[SALIDAS];



/*
 * This functions reads spectrometer data from SPEC_VIDEO
 * Look at the Timing Chart in the Datasheet for more info
 */
void readSpectrometer(int bande){

  int delayTime = 5; // delay time, 1 original.

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
void printData(int datsel){

  //Primero procesa la informacion para reducir a 50 longitudes de onda.

  //Para el caso de dispersion de luz

    if(datsel==0){
    //seleccion de datos especificos
    int corr=80;
    int ancho=50; 

     for (int i=50; i<61; i++){
      pdata[i-50]=data[i];
    }
    
    for (int i=85; i<126; i++){    //85 y 126
      pdata[i-75]=data[i];         //75
    }
  }

    if(datsel==1){
    //SELECCION DE DATOS ESPECIFICOS
    int corr=125;
    int ancho=50;

     for (int i=80; i<106; i++){
      pdata[i-80]=data[i];
    }
    for (int i=135; i<161; i++){
      pdata[i-110]=data[i];
    }

    
    //pdata[0]=550;
    //pdata[1]=550;
    //pdata[2]=550;
    
  
    //for (int i=19; i<30; i++){
    //  pdata[i]=550;
    //}
 
    //for (int i=42; i<50; i++){
    //  pdata[i]=550;
    //}

    
     //for (int i=0; i<50; i++){
     // pdata[i]=0;
    //}
    
  }



  //Solo saca 50 datos ya procesados
  
  for (int i = 0; i < SALIDAS; i++){
 
    Serial.print(pdata[i]);
    Serial.print(',');
    
  }

  Serial.println(" ");

  
}






void leeSpec(int tiint, int nuvec, int dsel){

  //Borra acumulador

   for (int i = 0; i < SPEC_CHANNELS; i++){
    dataacu[i]=0;
    } 

  delay(1000);    //Espera que estabilice la luz.
  
  for (int ki=0; ki<nuvec; ki++){
  readSpectrometer(0);
  delay(tiint);
  delayMicroseconds(100);     //Ligero extra para dispersion de luz, antes 730
  readSpectrometer(1);
   
  

  //Acumula

   for (int i = 0; i < SPEC_CHANNELS; i++){
    dataacu[i]=dataacu[i]+data[i];
    } 
  
  }

   //Promedia
   for (int i = 0; i < SPEC_CHANNELS; i++){
    data[i]=dataacu[i]/nuvec;
    } 
 

   //Normaliza pico, saca el pico del promedio de los 9 valores mas altos.

   
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
    data[i]=(10000*(data[i]/vmax5));
    }  
    
  
  printData(dsel);
  
}


//*******************************************************************************************************
