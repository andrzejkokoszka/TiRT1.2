#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from ComssServiceDevelopment.service import Service, ServiceController #import modułów klasy bazowej Service oraz kontrolera usługi
from custom_connectors.client_connectors import InputObjectClientConnector, InputMessageClientConnector, OutputObjectClientConnector, OutputMessageClientConnector
from PIL import Image, ImageTk, ImageEnhance

import numpy as np
import math

class ContrastService(Service): #klasa usługi musi dziedziczyć po ComssServiceDevelopment.service.Service
    def __init__(self):			#"nie"konstruktor, inicjalizator obiektu usługi
        super(ContrastService, self).__init__() #wywołanie metody inicjalizatora klasy nadrzędnej
        self.service_lock = threading.RLock() #obiekt pozwalający na blokadę wątku
        self.settings = None
        self.video_frame = None
        self.this_settings = {}
        # self.this_settings to słownik, który zawiera parametry tylko dla tego konkretnego serwisu. Składa się z trzech
        # elementów:
        # - minContrastIndex (double), minimalna wartość kontrastu, jaką można wybrać suwakiem w serwisie inputService
        # - maxContrastIndex (double), maksymalna wartość kontrastu, jaką można wybrać suwakiem w serwisie inputService
        # - contrastIndex (double), aktualnie wybrana wartość suwaka (współczynnik kontrastu)

        ## Zakres suwaka reprezentowany przez minContrastIndex i maxContrastIndex jest przetwarzany za
        ## pomocą innej funkcji matematycznej, bo stosowanie liniowego wzrostu wartości daje zbyt silne zmiany
        ## kontrastu przy duzych wartościach współczynnika kontrastu z suwaka i zbyt słabe zmiany przy małych
        ## wartościach. Do przetworzenia "dziedziny" wartości z suwaka służy funkcja self.get_contrast_factor

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
                self.this_settings = settings["contrastService"]


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

        image = Image.fromarray(frame)
        enhancer = ImageEnhance.Contrast(image)
        factor = self.get_contrast_factor()
        image = enhancer.enhance(factor)
        frame = np.array(image)
        return frame

    def get_contrast_factor(self):
        contrast_index = self.this_settings["contrastIndex"]
        min_index = self.this_settings["minContrastIndex"]
        max_index = self.this_settings["maxContrastIndex"]
        if contrast_index < 0:
            return -1/min_index*contrast_index + 1
        else:
            a = 0.985
            f = lambda x: (x/math.sqrt(1-math.pow(x,2)))
            return f(contrast_index/max_index*a)/f(a)*14+1

    def run(self):	#główna metoda usługi
        threading.Thread(target=self.read_settings).start()
        threading.Thread(target=self.read_video).start()
        threading.Thread(target=self.send_settings).start()
        self.send_video()


if __name__=="__main__":
    sc = ServiceController(ContrastService, "contrastService.json") #utworzenie obiektu kontrolera usługi
    sc.start() #uruchomienie usługi