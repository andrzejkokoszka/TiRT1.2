#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import socket


class DevServiceController(object):
    def __init__(self, service_desc_path):
        with open(service_desc_path, 'r') as f:
            self.service_conf = json.load(f)
        self.connections = {}

    def declare_connection(self, connection_id, connection):
        if connection_id in self.service_conf.get('inputs', {}):
            connection.set_params(self.service_conf['inputs'][connection_id])
            connection.init()

        elif connection_id in self.service_conf.get('outputs', {}):
            connection.set_params(self.service_conf['outputs'][connection_id])
            connection.init()
        else:
            pass
        self.connections[connection_id] = connection

    def get_connection(self, connection_id):
        return self.connections[connection_id]

    def update_params(self, new_params):
        host, port = self.service_conf['parametersHost'].split(':')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, int(port)))
        s.sendall(json.dumps(new_params) + '\n')
        s.close()