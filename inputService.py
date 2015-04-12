#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ComssServiceDevelopment.service import Service, ServiceController #import modułów klasy bazowej Service oraz kontrolera usługi
from custom_connectors.client_connectors import OutputMessageClientConnector, OutputObjectClientConnector
from parameters import ServicesParameters
from inputApp import Application
import os, signal
import threading
import cv2 #import modułu biblioteki OpenCV
import time

class InputService(Service): #klasa usługi musi dziedziczyć po ComssServiceDevelopment.service.Service
    def __init__(self):			#"nie"konstruktor, inicjalizator obiektu usługi
        super(InputService, self).__init__() #wywołanie metody inicjalizatora klasy nadrzędnej

        self.service_params = ServicesParameters()
        self.webCam = cv2.VideoCapture(0) # strumien z kamery wideo
        self.service_lock = threading.RLock() #obiekt pozwalający na blokadę wątku

        self.app = Application()

    def declare_outputs(self):	#deklaracja wyjść
        self.declare_output("videoOutput", OutputMessageClientConnector(self))
        self.declare_output("settingsOutput", OutputObjectClientConnector(self))

    def declare_inputs(self): #deklaracja wejść
        pass

    def run_app_gui(self):
        self.app.master.title('Input settings')
        self.app.mainloop()
        os.kill(os.getpid(),signal.SIGTERM)

    def send_settings(self):
        settings_output = self.get_output("settingsOutput") # obiekt interfejsu wyjściowego dla ustawień

        while self.running():
            with self.service_lock:     #blokada wątku
                ## Pobieram wartości widgetów z interfejsu graficznego
                # zmienne dotyczące serwisu resizeService :
                resize_service = self.app.var_checkbox_resize.get()
                resize_coeff = self.app.var_scale_resize.get()
                # zmienne dotyczące serwisu filterGrayService :
                filter_gray_service = self.app.var_checkbox_filterGray.get()
                # zmienne dotyczące serwisu brightnessService :
                brightness_service = self.app.var_checkbox_brightness.get()
                brightness_index = self.app.var_scale_brightness.get()
                min_brightness_index = self.app.scale_brightness.cget('from')
                max_brightness_index = self.app.scale_brightness.cget('to')
                # zmienne dotyczące serwisu contrastService :
                contrast_service = self.app.var_checkbox_contrast.get()
                contrast_index = self.app.var_scale_contrast.get()
                min_contrast_index = self.app.scale_contrast.cget('from')
                max_contrast_index = self.app.scale_contrast.cget('to')

            # Określam, które serwisy trzeba zastosować - dodaje do kolekcji numery ID poszczególnych serwisów, które należy wykonać
            services_applied = set()
            services_applied.add(self.service_params.getServiceValue(self.service_params.PREPROCESSING_SERVICE)) # serwis preprocessingu wykonywany jest zawsze
            if resize_service:
                services_applied.add(self.service_params.getServiceValue(self.service_params.RESIZE_SERVICE))
            if filter_gray_service:
                services_applied.add(self.service_params.getServiceValue(self.service_params.FILTER_GRAY_SERVICE))
            if brightness_service:
                services_applied.add(self.service_params.getServiceValue(self.service_params.BRIGHTNESS_SERVICE))
            if contrast_service:
                services_applied.add(self.service_params.getServiceValue(self.service_params.CONTRAST_SERVICE))

            # Tworzę słownik z ustawieniami, który będzie przesłany do serwisu master
            settings = {'servicesApplied': list(services_applied),
                        'resizeCoeff': resize_coeff,
                        'contrastService': {
                            "contrastIndex": contrast_index,
                            "minContrastIndex": min_contrast_index,
                            "maxContrastIndex": max_contrast_index
                        },
                        'brightnessService': {
                            "brightnessIndex": brightness_index,
                            "minBrightnessIndex": min_brightness_index,
                            "maxBrightnessIndex": max_brightness_index
                        }
                       }

            settings_output.send(settings) # wysłanie ustawień do serwisu master
            #print "ustawienia wysłane:", settings

            time.sleep(0.05)

    def send_video(self):
        video_output = self.get_output("videoOutput") # obiekt interfejsu wyjściowego dla obrazu

        while self.running():

            _, frame = self.webCam.read() # odczyt obrazu z kamery
            frame_dump = frame.dumps() # zrzut ramki wideo do postaci ciągu bajtow

            video_output.send(frame_dump) # przesłanie ramki video do serwisu master
            #print "ramka wysłana"
            time.sleep(0.05)

    def run(self):	#główna metoda usługi
        threading.Thread(target=self.run_app_gui).start() # W oddzielnym wątku uruchamiam aplikację z iterfejsem graficzynym
        threading.Thread(target=self.send_settings).start()
        threading.Thread(target=self.send_video).start()

        while self.running():   # pętla główna usługi
            pass

if __name__=="__main__":
    sc = ServiceController(InputService, "inputService.json") #utworzenie obiektu kontrolera usługi
    sc.start() #uruchomienie usługi