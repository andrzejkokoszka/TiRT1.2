#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ComssServiceDevelopment.service import Service, ServiceController #import modułów klasy bazowej Service oraz kontrolera usługi
from custom_connectors.server_connectors import InputMessageServerConnector, InputObjectServerConnector, OutputMessageServerConnector, OutputObjectServerConnector
from parameters import ServicesParameters

import threading
import numpy as np #import modułu biblioteki Numpy
import time

class MasterService(Service):
    def __init__(self): # "nie"konstruktor, inicjalizator obiektu usługi
        super(MasterService, self).__init__() # wywołanie metody inicjalizatora klasy nadrzędnej
        self.service_lock = threading.RLock() # obiekt pozwalający na blokadę wątku
        self.service_params = ServicesParameters() # obiekt do pobierania nazw serwisów, które podłączone są do serwisu master i ich konektorów
        self.next_services = {} # słownik, którego elementy maja następujący format: { nazwa_serwisu_1 : nazwa_serwisu_2 }, gdzie nazwa_serwisu_2 jest stringiem określającym serwis, do którego zostaje przesłany obraz po powrocie do mastera z serwisu określonego jako nazwa_serwisu_1. Zmienna ta bezpośrednio określa kolejność wykonywania poszczególnych serwisów.
        self.video_frames = {}  # słownik z elementami formatu: { nazwa_serwisu : obraz_z_kamery } - zawiera zrzuty z ekranu, które mają być przesyłane do poszczególnych serwisów określonych jako string nazwa_serwisu
        self.settings = {}  # słownik z elementami formatu: { nazwa_serwisu : słownik_z_ustawieniami } - zawiera ustawienia, które mają być przesłane do kolejnych serwisów określonych jako nazwa_serwisu

        self.__prepare_instance()   # przygotowanie zmiennych self.next_services, self.video_frames i self.settings - należy dodać odpowiednie klucze (nazwy serwisów) w słownikach

    def __prepare_instance(self):
        services_names = self.service_params.getAllServiceNames() # pobranie nazw wszsytkich serwisów podpiętych do mastera
        for service in services_names:
            self.next_services[service] = None
            self.video_frames[service] = None
            self.settings[service] = None

    def declare_outputs(self):	# deklaracja wyjść
        service_names = self.service_params.getAllServiceNames() # pobieram nazwy wszystkich serwisów, jakie będą podłączone do serwisu master (na ich podstawie są pobierane nazy konektorów)
        for service in service_names:
            connector_name = self.service_params.getOutputVideoConnectorName(service) # pobieram nazwę konektora wyjściowego dla obrazu video
            self.declare_output(connector_name, OutputMessageServerConnector(self)) # deklaracja konektora
            connector_name = self.service_params.getOutputSettingsConnectorName(service) # pobieram nazwę konektora wyjściowego dla ustawień przetwarzania
            self.declare_output(connector_name, OutputObjectServerConnector(self)) # deklaracja konektora

    def declare_inputs(self): #deklaracja wejść
        service_names = self.service_params.getAllServiceNames() # pobieram nazwy wszystkich serwisów, jakie będą podłączone do serwisu master (na ich podstawie są pobierane nazy konektorów)
        for service in service_names:
            connector_name = self.service_params.getInputVideoConnectorName(service) # pobieram nazwę konektora wejściowego dla obrazu video
            self.declare_input(connector_name, InputMessageServerConnector(self)) # deklaracja konektora
            connector_name = self.service_params.getInputSettingsConnectorName(service) # pobieram nazwę konektora wejściowego dla ustawień przetwarzania
            self.declare_input(connector_name, InputObjectServerConnector(self)) # deklaracja konektora

    def read_settings(self, service_name, str_settingsInput):
        settings_input = self.get_input(str_settingsInput) # obiekt interfejsu wejściowego

        while self.running():

            settings = settings_input.read() #odczyt danych z interfejsu wejściowego
            #print service_name, ": odebrano ustwienia:", settings
            services_to_apply = settings['servicesApplied'] # lista serwisów, które należy wykorzystać. Zawiera numery ID, które określone są w klasie ServiceParameters, zmiennej SERVICES_ID

            if services_to_apply: # jeśli lista serwisów nie jest pusta, to trzeba przekazac dane do kolejnego serwisu
                next_service_value = services_to_apply.pop(0) # biorę pierwszy element z listy serwisow - ta usługa będzie aktualnie zastosowana
            else: # jeśli lista serwisów jest pusta, to trzeba przekazać obraz na wyjście mastera
                next_service_value = self.service_params.getServiceValue(self.service_params.MASTER_SERVICE)

            next_service_name = self.service_params.getServiceName(next_service_value)
            settings['servicesApplied'] = services_to_apply # aktualizuję ogólne ustawienia z usuniętym pierwszym elementem

            with self.service_lock:
                self.settings[next_service_name] = settings
                self.next_services[service_name] = next_service_name

    def send_settings(self, service_name, str_settingsOutput):
        settings_output = self.get_output(str_settingsOutput)

        while self.running():
            if not self.settings[service_name] is None:
                settings_output.send(self.settings[service_name])
                #print service_name, ": ustawienia wysłane"
                with self.service_lock:
                    self.settings[service_name] = None

    def read_video(self, service_name, str_videoInput):
        video_input = self.get_input(str_videoInput)

        while self.running():
            frame_obj = video_input.read()  # odebranie danych z interfejsu wejściowego dla obrazu
            #print service_name, ": odebrano ramkę"
            frame = np.loads(frame_obj) # załadowanie ramki do obiektu NumPy
            frame = frame.dumps()

            with self.service_lock:
                next_service_name = self.next_services[service_name]
                self.video_frames[next_service_name] = frame

    def send_video(self, service_name, str_videoInput):
        video_output = self.get_output(str_videoInput)

        while self.running():
            if not self.video_frames[service_name] is None:
                video_output.send(self.video_frames[service_name]) #przesłanie ramki za pomocą interfejsu wyjściowego
                #print service_name, ": ramka wysłana"
                with self.service_lock:
                    self.video_frames[service_name] = None


    def run(self):	# główna metoda usługi
        # Uruchamiam w odzielnych wątkach metody obsługujące wejścia i wyjścia serwisów podrzędnych, które podłączone są do mastera
        for service_name in self.service_params.getAllServiceNames():
            input_settings_connector = self.service_params.getInputSettingsConnectorName(service_name) # pobieram nazwę konektora wejściowego serwisu podrzędnego (wejście ustawień)
            threading.Thread(target=lambda: self.read_settings(service_name, input_settings_connector)).start()

            input_video_connector = self.service_params.getInputVideoConnectorName(service_name) # pobieram nazwę konektora wejściowego serwisu podrzędnego (wejście obrazu)
            threading.Thread(target=lambda: self.read_video(service_name, input_video_connector)).start() #uruchomienie wątku obsługującego wejścia i wyjścia dla serwisu podrzędnego

            output_settings_connector = self.service_params.getOutputSettingsConnectorName(service_name)
            threading.Thread(target=lambda: self.send_settings(service_name, output_settings_connector)).start()

            output_video_connector = self.service_params.getOutputVideoConnectorName(service_name)
            threading.Thread(target=lambda: self.send_video(service_name, output_video_connector)).start()

        while self.running():
            pass

if __name__=="__main__":
    sc = ServiceController(MasterService, "masterService.json") #utworzenie obiektu kontrolera usługi
    sc.start() #uruchomienie usługi