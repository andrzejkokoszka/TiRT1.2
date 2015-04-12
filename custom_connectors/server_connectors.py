#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import socket
import time
import json

from ComssServiceDevelopment.connectors.base import BaseConnector

# if you catch one of these errors, beware - services can be screwed up, but try again - maybe just connections problems
SOCKET_ERRORS_TO_RETRY = [9, 32, 104, 109, 111, 10054, 10061]
# if you catch one of these errors, its ok - just continue
SOCKET_ERRORS_TO_PASS = [4]

MSG_LENGTH_FORMAT = "l"
MSG_LENGTH_BYTES = struct.calcsize(MSG_LENGTH_FORMAT)

class OutputStreamServerConnector(BaseConnector):

    SEND_TRY_INTERVAL = 3
    MAX_SEND_RETRIES = 10
    SEND_TIMEOUT = 10
    SOCKET_TIMEOUT = 20

    def __init__(self, service_instance):
        super(OutputStreamServerConnector,self).__init__(service_instance)
        self.server_socket = None
        self._params = {}
        self.client_socket = None

    def set_params(self, params):
        self._params = params

    def get_output_ip(self):
        return self._params['ip']

    def get_output_port(self):
        return self._params['port']

    def init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.get_output_ip(), self.get_output_port()))
        self.server_socket.listen(1)

    def prepare_client_socket(self):
        if self.client_socket is None:
            self.client_socket, _ = self.server_socket.accept()

    def clear_client_socket_connection(self):
        try:
            self.client_socket.close()
        except:
            pass
        self.client_socket = None

    def send(self, data):
        counter = self.MAX_SEND_RETRIES
        while True:
            try:
                self.prepare_client_socket()
                self.client_socket.send(data)
            except Exception as e:
                if getattr(e, 'errno', None) is None:
                    raise e
                if not e.errno in SOCKET_ERRORS_TO_RETRY or counter <= 0:
                    raise e
                counter -= 1
                self.clear_client_socket_connection()
                time.sleep(self.SEND_TRY_INTERVAL)
            else:
                break

    def close(self):
        self.clear_client_socket_connection()


class OutputMessageServerConnector(OutputStreamServerConnector):
    def send(self, message):
        message_length = len(message)
        super(OutputMessageServerConnector, self).send(struct.pack(MSG_LENGTH_FORMAT, message_length))
        super(OutputMessageServerConnector, self).send(message)


class OutputObjectServerConnector(OutputMessageServerConnector):
    def send(self, obj):
        dumped_object = json.dumps(obj)
        super(OutputObjectServerConnector, self).send(dumped_object)



# Ten teraz edytuję
class InputStreamServerConnector(BaseConnector):
    READ_TRY_INTERVAL = 3
    MAX_READ_RETRIES = 10
    SOCKET_TIMEOUT = 20

    def __init__(self, service_instance):
        super(InputStreamServerConnector,self).__init__(service_instance)
        self.server_socket = None
        self._params = {}
        self.client_socket = None
        self.client_socket_as_file = None

    def set_params(self, params):
        self._params = params

    def get_input_ip(self):
        return self._params['ip']

    def get_input_port(self):
        return self._params['port']

    def init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.get_input_ip(), self.get_input_port()))
        self.server_socket.listen(1)

    def prepare_client_socket(self):
        if self.client_socket is None:
            self.client_socket, _ = self.server_socket.accept()
            self.client_socket_as_file = self.client_socket.makefile()

    def clear_client_socket_connection(self):
        try:
            self.client_socket.close()
        except:
            pass
        self.client_socket = None
        self.client_socket_as_file = None

    def read(self, recv_buffer=1024):
        counter = self.MAX_READ_RETRIES
        while True:
            try:
                self.prepare_client_socket()
                read_buffer = self.client_socket.recv(recv_buffer)
            except Exception as e:
                if not e.errno in SOCKET_ERRORS_TO_RETRY or counter <= 0:
                    raise e
                counter -= 1
                self.clear_client_socket_connection()
            else:
                if not read_buffer:
                    counter -= 1
                    self.clear_client_socket_connection()
                else:
                    return read_buffer

    def close(self):
        self.clear_client_socket_connection()


class InputMessageServerConnector(InputStreamServerConnector):

    def read_message(self):
        super(InputMessageServerConnector, self).prepare_client_socket()
        message_size_msg = self.client_socket_as_file.read(MSG_LENGTH_BYTES)
        try:
            message_size = struct.unpack(MSG_LENGTH_FORMAT, message_size_msg)[0]
            message = self.client_socket_as_file.read(message_size)
            return message
        except struct.error:
            return None

    def read(self):
        counter = super(InputMessageServerConnector, self).MAX_READ_RETRIES
        while True:
            try:
                read_buffer = self.read_message()
            except Exception as e:
                __errno = getattr(e, 'errno', None)
                if __errno is  None:
                    raise
                elif __errno in SOCKET_ERRORS_TO_PASS:
                    continue
                elif not e.errno in SOCKET_ERRORS_TO_RETRY or counter <= 0:
                    raise e
                counter -= 1
                super(InputMessageServerConnector, self).clear_client_socket_connection()
            else:
                if not read_buffer:
                    counter -= 1
                    super(InputMessageServerConnector, self).clear_client_socket_connection()
                else:
                    return read_buffer


class InputObjectServerConnector(InputMessageServerConnector):
    def read(self):
        msg = super(InputObjectServerConnector, self).read()
        return json.loads(msg)