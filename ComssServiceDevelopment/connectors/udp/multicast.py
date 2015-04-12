#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import struct
import marshal
from ComssServiceDevelopment.connectors.base import BaseConnector


class OutputMulticastConnector(BaseConnector):

    TIMEOUT = 0.2
    TTL = 2

    def __init__(self, service_instance):
        self._service_instance = service_instance
        self.sock = None
        self._params = {}

    def init(self):
        pass

    def close(self):
        self.__close_socket()

    def set_params(self, params):
        self._params = params

    def get_multicast_ip(self):
        return self._params['ip']

    def get_multicast_port(self):
        return self._params['port']

    def __open_socket(self):
        if self.sock is None:
            self.multicast_group = (self.get_multicast_ip(), self.get_multicast_port())
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(OutputMulticastConnector.TIMEOUT)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b',OutputMulticastConnector.TTL))

    def __close_socket(self):
        try:
            self.sock.close()
        except:
            pass
        self.sock = None

    def send(self, msg):
        self.__open_socket()
        dumped_msg = marshal.dumps(msg)
        try:
            self.sock.sendto(dumped_msg, self.multicast_group)
        except:
            pass


class InputMulticastConnector(BaseConnector):

    TIMEOUT = 0.2
    TTL = 2

    def __init__(self, service_instance):
        self._service_instance = service_instance
        self.sock = None
        self._params = {}

    def init(self):
        pass

    def close(self):
        self.__close_socket()

    def set_params(self, params):
        self._params = params

    def get_multicast_ip(self):
        return self._params['ip']

    def get_multicast_port(self):
        return self._params['port']

    def __open_socket(self):
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                pass # Some systems don't support SO_REUSEPORT
            self.sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, 20)
            self.sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

            # Bind to the port
            self.sock.bind((self.get_multicast_ip(), self.get_multicast_port()))
            # Tell the operating system to add the socket to the multicast group
            # on all interfaces.
            group = socket.inet_aton(self.get_multicast_ip())
            # mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            # self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def __close_socket(self):
        self.sock.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP, socket.inet_aton(self.address) + socket.inet_aton('0.0.0.0'))
        self.sock.close()
        self.sock = None

    def read(self, buf_size=4096):
        self.__open_socket()
        data, sender_addr = self.sock.recvfrom(buf_size)
        return marshal.loads(data)