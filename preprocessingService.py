#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from ComssServiceDevelopment.service import Service, ServiceController #import modułów klasy bazowej Service oraz kontrolera usługi
from custom_connectors.client_connectors import InputMessageClientConnector, InputObjectClientConnector, OutputMessageClientConnector, OutputObjectClientConnector
from custom_connectors.server_connectors import OutputMessageServerConnector
import cv2 #import modułu biblioteki OpenCV
import numpy as np #import modułu biblioteki Numpy

class PreprocessingService(Service):
    """
    Serwis służy do przywracania naturalnego koloru dla obrazu video oraz obraca go w poziomie.
    Ma dwa wyjścia obrazu - jedno przekazuje obraz do mastera do koljnego przetwarzania, drugie podaje obraz
    bezpośrednio na wyjście.
    """
    def __init__(self):			#"nie"konstruktor, inicjalizator obiektu usługi
        super(PreprocessingService, self).__init__() #wywołanie metody inicjalizatora klasy nadrzędnej
        self.service_lock = threading.RLock() #obiekt pozwalający na blokadę wątku
        self.settings = None
        self.video_frame_output = None
        self.video_frame_master = None

    def declare_outputs(self):	#deklaracja wyjść
        self.declare_output("videoOutputMaster", OutputMessageClientConnector(self))
        self.declare_output("videoOutputOutput", OutputMessageServerConnector(self))
        self.declare_output("settingsOutput", OutputObjectClientConnector(self))

    def declare_inputs(self): #deklaracja wejść
        self.declare_input("videoInput", InputMessageClientConnector(self))
        self.declare_input("settingsInput", InputObjectClientConnector(self))

    def read_settings(self):
        settings_input = self.get_input("settingsInput") #obiekt interfejsu wejściowego
        while self.running():
            settings = settings_input.read()
            #print "ustawienia odebrane:", settings
            with self.service_lock:  #blokada wątku
                self.settings = settings

    def send_settings(self):
        settings_output = self.get_output("settingsOutput") #obiekt interfejsu wyjściowego
        while self.running():

            if not self.settings is None:
                settings_output.send(self.settings) #przesłanie danych za pomocą interfejsu wyjściowego
                #print "ustawienia wysłane:", self.settings
                with self.service_lock:
                    self.settings = None

    def read_video(self):
        video_input = self.get_input("videoInput")	#obiekt interfejsu wejściowego
        while self.running():   #pętla główna usługi
            frame_obj = video_input.read()  #odebranie danych z interfejsu wejściowego
            #print "ramka odebrana"
            frame = np.loads(frame_obj)     #załadowanie ramki do obiektu NumPy

            frame = self.process_frame(frame)

            frame = frame.dumps()
            with self.service_lock:
                self.video_frame_output = frame
                self.video_frame_master = frame

    def send_video_to_output(self):
        video_output = self.get_output("videoOutputOutput") #obiekt interfejsu wyjściowego
        while self.running():
            if not self.video_frame_output is None:
                video_output.send(self.video_frame_output) #przesłanie ramki za pomocą interfejsu wyjściowego
                #print "ramka wysłana na output"
                with self.service_lock:
                    self.video_frame_output = None

    def send_video_to_master(self):
        video_output = self.get_output("videoOutputMaster") #obiekt interfejsu wyjściowego
        while self.running():
            if not self.video_frame_master is None:
                video_output.send(self.video_frame_master) #przesłanie ramki za pomocą interfejsu wyjściowego
                #print "ramka wysłana na master"
                with self.service_lock:
                    self.video_frame_master = None

    def process_frame(self, frame):
        frame = cv2.flip(frame, 1) # odwrócenie ramki w poziomie
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # przywrocenie naturalnych kolorów
        frame = cv2.resize(frame, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)
        return frame

    def run(self):	#główna metoda usługi
        threading.Thread(target=self.read_settings).start()
        threading.Thread(target=self.read_video).start()
        threading.Thread(target=self.send_settings).start()
        threading.Thread(target=self.send_video_to_output).start()
        self.send_video_to_master()


if __name__=="__main__":
    sc = ServiceController(PreprocessingService, "preprocessingService.json") #utworzenie obiektu kontrolera usługi
    sc.start() #uruchomienie usługi
