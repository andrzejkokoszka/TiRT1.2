#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from ComssServiceDevelopment.service import Service, ServiceController #import modułów klasy bazowej Service oraz kontrolera usługi
from custom_connectors.client_connectors import InputMessageClientConnector
from outputApp import Application
from PIL import Image, ImageTk
import os, signal
import numpy as np #import modułu biblioteki Numpy

class OutputService(Service): #klasa usługi musi dziedziczyć po ComssServiceDevelopment.service.Service
    def __init__(self):			#"nie"konstruktor, inicjalizator obiektu usługi
        super(OutputService, self).__init__() #wywołanie metody inicjalizatora klasy nadrzędnej
        self.service_lock = threading.RLock() #obiekt pozwalający na blokadę wątku
        self.app = Application()

    def declare_outputs(self):	#deklaracja wyjść
        pass

    def declare_inputs(self): #deklaracja wejść
        self.declare_input("videoInputOrigin", InputMessageClientConnector(self))
        self.declare_input("videoInputModified", InputMessageClientConnector(self))

    def run_app_gui(self):
        self.app.master.title('Output service')
        self.app.mainloop()
        os.kill(os.getpid(), signal.SIGTERM)

    def read_and_show_frame(self, input_connector, video_frame_label):
        while self.running():
            with self.service_lock:
                obj = input_connector.read()
                #print "odebrano ramkę:", input_connector
                frame = np.loads(obj) # załadownaie ramki do obiektu NumPy
                img = Image.fromarray(frame)
                imgTk = ImageTk.PhotoImage(image=img)
                video_frame_label.imgTk = imgTk
                video_frame_label.configure(image=imgTk)

    def run(self):	#główna metoda usługi
        video_input_origin = self.get_input("videoInputOrigin") # obiekt interfejsu wyjściowego dla obrazu oryginalnego
        video_input_modified = self.get_input("videoInputModified") # obiekt interfejsu wyjściowego dla obrazu zmodyfikowanego

        threading.Thread(target=self.run_app_gui).start() # uruchomienie wątku obsługującego panel GUI
        threading.Thread(target=lambda: self.read_and_show_frame(video_input_origin, self.app.label_videoOrigin)).start()
        threading.Thread(target=lambda: self.read_and_show_frame(video_input_modified, self.app.label_videoModified)).start()

        while self.running():
            pass


if __name__=="__main__":
    sc = ServiceController(OutputService, "outputService.json") #utworzenie obiektu kontrolera usługi
    sc.start() #uruchomienie usługi