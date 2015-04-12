#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from ComssServiceDevelopment.connectors.tcp.msg_stream_connector import InputMessageConnector, OutputMessageConnector


class OutputObjectConnector(OutputMessageConnector):
    def send(self, obj):
        self.check_socket_and_open()
        dumped_object = json.dumps(obj)
        super(OutputObjectConnector, self).send(dumped_object)


class InputObjectConnector(InputMessageConnector):
    def read(self):
        msg = super(InputObjectConnector, self).read()
        return json.loads(msg)