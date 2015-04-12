#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from ComssServiceDevelopment.service import Service, ServiceController #import modułów klasy bazowej Service oraz kontrolera usługi
from custom_connectors.client_connectors import OutputMessageClientConnector, OutputObjectClientConnector, InputMessageClientConnector,InputObjectClientConnector
import cv2 #import modułu biblioteki OpenCV
import numpy as np #import modułu biblioteki Numpy

class ResizeService(Service):
    def __init__(self):			#"nie"konstruktor, inicjalizator obiektu usługi
        super(ResizeService, self).__init__() #wywołanie metody inicjalizatora klasy nadrzędnej
        self.service_lock = threading.RLock() #obiekt pozwalający na blokadę wątku
        self.settings = None
        self.video_frame = None
        self.resize_coeff = None

    def declare_outputs(self):	#deklaracja wyjść
        self.declare_output("videoOutput", OutputMessageClientConnector(self))
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
                self.resize_coeff = settings["resizeCoeff"]

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
                self.video_frame = frame

    def send_video(self):
        video_output = self.get_output("videoOutput") #obiekt interfejsu wyjściowego
        while self.running():
            if not self.video_frame is None:
                video_output.send(self.video_frame) #przesłanie ramki za pomocą interfejsu wyjściowego
                #print "ramka wysłana"
                with self.service_lock:
                    self.video_frame = None

    def process_frame(self, frame):
        resize_coeff = self.resize_coeff
        return cv2.resize(frame, None, fx=resize_coeff, fy=resize_coeff, interpolation=cv2.INTER_AREA)

    def run(self):	#główna metoda usługi
        threading.Thread(target=self.read_settings).start()
        threading.Thread(target=self.read_video).start()
        threading.Thread(target=self.send_settings).start()
        self.send_video()


if __name__=="__main__":
    sc = ServiceController(ResizeService, "resizeService.json") #utworzenie obiektu kontrolera usługi
    sc.start() #uruchomienie usługi
