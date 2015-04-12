#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import signal
import threading
import socket
from ComssServiceDevelopment.utils import ServiceCommunicationWatcherThread


class Service(object):
    def __init__(self):
        self.inputs = {}
        self.outputs = {}
        self.__started = False
        self.__running = False
        self.__params = {}
        self.param_watcher = ServiceCommunicationWatcherThread(self)
        self.logger = logging.getLogger("logger")
        self.update_params_host = None
        self.param_port = None
        self.__param_socket = None

    def declare_inputs(self):
        raise NotImplementedError()

    def declare_outputs(self):
        raise NotImplementedError()

    def declare_input(self, key, service_input):
        if self.__started:
            self.logger.error("Cannot declare input during runtime")
        elif key in self.inputs:
            raise Exception("There is already an input with given ID")
        else:
            self.inputs[key] = service_input

    def declare_output(self, key, service_output):
        if self.__started:
            self.logger.error("Cannot declare output during runtime")
        elif key in self.outputs:
            raise Exception("There is already an output with given ID")
        else:
            self.outputs[key] = service_output

    def get_parameter(self, key):
        return self.__params[key]

    def get_input(self, key):
        return self.inputs[key]

    def get_output(self, key):
        return self.outputs[key]

    def running(self):
        return self.__running

    def run(self):
        raise NotImplementedError()

    def start(self):
        self.__started = True
        self.__running = True
        self.param_watcher.start()
        self.run()

    def stop(self):
        self.__running = False
        self.__param_socket.close()
        for _, inst in self.inputs.iteritems():
            inst.stop()
        for _, inst in self.outputs.iteritems():
            inst.stop()

    def update_parameters(self, params):
        self.__params.update(params)

class ServiceController(object):
    def __init__(self, service_class, desc_path):
        self.service_class = service_class
        with open(desc_path, 'r') as f:
            self.service_desc = json.load(f)
        self.service = None
    
    def start(self):
        self.service = self.service_class()
        self.service.update_params_host = self.service_desc["parametersHost"]
        self.service.update_parameters(self.service_desc.get("parameters", {}))
        self.service.declare_inputs()
        for _input_id, _input_params in self.service_desc.get("inputs").iteritems():
            self.service.inputs[_input_id].set_params(_input_params)
            self.service.inputs[_input_id].init()

        self.service.declare_outputs()
        for _output_id, _output_params in self.service_desc.get("outputs").iteritems():
            self.service.outputs[_output_id].set_params(_output_params)
            self.service.outputs[_output_id].init()

        try:
            signal.signal(signal.SIGTERM, lambda *args, **kwargs: self.service.stop())
            self.service.start()
        except:
            raise
        finally:
            try:
                self.service.stop()
            except:
                pass