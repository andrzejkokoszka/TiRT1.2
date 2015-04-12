#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseConnector(object):
    def __init__(self, service_instance, *args, **kwargs):
        self.service_instance = service_instance

    def init(self):
        raise NotImplementedError()

    def set_params(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()