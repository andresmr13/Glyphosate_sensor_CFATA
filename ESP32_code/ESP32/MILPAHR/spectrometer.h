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
  SULI=0;
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

void leeSpec(int tiint, int nuvec){

  //Borra acumulador

   for (int i = 0; i < SPEC_CHANNELS; i++){
    dataacu[i]=0;
    } 

  for (int ki=0; ki<nuvec; ki++){
  
  readSpectrometer(0);
  delay(tiint);
  readSpectrometer(1);
  //prende de nuevo laser
  ledcWrite(2,850);
  SULI=1200;
  
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
  
  //Normaliza pico

    float vmax=0;
    
    for (int i = 0; i < SPEC_CHANNELS; i++){
    if (data[i]>vmax){
      vmax=data[i];
    }
    }

    for (int i = 0; i < SPEC_CHANNELS; i++){
    data[i]=(1000*(data[i]/vmax));
    }  

  //Acumula

   for (int i = 0; i < SPEC_CHANNELS; i++){
    dataacu[i]=dataacu[i]+data[i];
    } 
  
  }

   //Promedia
   for (int i = 0; i < SPEC_CHANNELS; i++){
    data[i]=dataacu[i]/nuvec;
    } 
  

  
  printData();
  
}


//*******************************************************************************************************
