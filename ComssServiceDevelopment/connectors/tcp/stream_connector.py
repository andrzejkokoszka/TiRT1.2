#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time

# if you catch one of these errors, beware - services can be screwed up, but try again - maybe just connections problems
from ComssServiceDevelopment.connectors.base import BaseConnector

SOCKET_ERRORS_TO_RETRY = [9, 32, 104, 109, 111]
# if you catch one of these errors, its ok - just continue
SOCKET_ERRORS_TO_PASS = [4]


class OutputStreamConnector(BaseConnector):

    SEND_TRY_INTERVAL = 3
    MAX_SEND_RETRIES = 10
    SEND_TIMEOUT = 10
    SOCKET_TIMEOUT = 20

    def __init__(self, service_instance):
        super(OutputStreamConnector,self).__init__(service_instance)
        self.socket = None
        self._params = {}

    def set_params(self, params):
        self._params = params

    def get_output_ip(self):
        return self._params['ip']

    def get_output_port(self):
        return self._params['port']

    def init(self):
        pass

    def __open_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.get_output_ip(), self.get_output_port()))
        self.socket = s

    def check_socket_and_open(self):
        if self.socket is None:
            self.__open_socket()

    def send(self, data):
        counter = self.MAX_SEND_RETRIES
        while True:
            try:
                self.check_socket_and_open()
                self.socket.send(data)
            except Exception as e:
                if getattr(e, 'errno', None) is None:
                    raise e
                if not e.errno in SOCKET_ERRORS_TO_RETRY or counter <= 0:
                    raise e
                counter -= 1
                self.close_socket()
                time.sleep(self.SEND_TRY_INTERVAL)
            else:
                break

    def close_socket(self):
        try:
            self.socket.close()
        except:
            pass
        self.socket = None

    def close(self):
        self.close_socket()


class InputStreamConnector(BaseConnector):
    READ_TRY_INTERVAL = 3
    MAX_READ_RETRIES = 10
    SOCKET_TIMEOUT = 20

    def __init__(self, service_instance):
        super(InputStreamConnector,self).__init__(service_instance)
        self.socket = None
        self._params = {}
        self.socket_connection = None
        self.socket_connection_as_file = None

    def set_params(self, params):
        self._params = params

    def get_input_ip(self):
        return self._params['ip']

    def get_input_port(self):
        return self._params['port']

    def init(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.get_input_ip(), self.get_input_port()))
        self.socket.listen(1)

    def prepare_socket_read(self):
        if self.socket_connection is None:
            self.socket_connection, addr = self.socket.accept()
            self.socket_connection_as_file = self.socket_connection.makefile()


    def clear_socket_connection(self):
        try:
            self.socket.close()
        except:
            pass
        self.socket_connection = None
        self.socket_connection_as_file = None

    def read(self, recv_buffer=1024):
        counter = self.MAX_READ_RETRIES
        while True:
            try:
                self.prepare_socket_read()
                read_buffer = self.socket_connection.recv(recv_buffer)
            except Exception as e:
                if not e.errno in SOCKET_ERRORS_TO_RETRY or counter <= 0:
                    raise e
                counter -= 1
                self.clear_socket_connection()
            else:
                if not read_buffer:
                    counter -= 1
                    self.clear_socket_connection()
                else:
                    return read_buffer

    def close(self):
        self.clear_socket_connection()