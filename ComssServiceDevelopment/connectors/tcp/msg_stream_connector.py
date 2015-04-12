#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
from ComssServiceDevelopment.connectors.tcp.stream_connector import InputStreamConnector, OutputStreamConnector, SOCKET_ERRORS_TO_PASS, SOCKET_ERRORS_TO_RETRY

MSG_LENGTH_FORMAT = "l"
MSG_LENGTH_BYTES = struct.calcsize(MSG_LENGTH_FORMAT)


class OutputMessageConnector(OutputStreamConnector):
    def send(self, message):
        self.check_socket_and_open()
        message_length = len(message)
        super(OutputMessageConnector, self).send(struct.pack(MSG_LENGTH_FORMAT, message_length))
        super(OutputMessageConnector, self).send(message)


class InputMessageConnector(InputStreamConnector):

    def read_message(self):
        super(InputMessageConnector, self).prepare_socket_read()
        message_size_msg = self.socket_connection_as_file.read(MSG_LENGTH_BYTES)
        try:
            message_size = struct.unpack(MSG_LENGTH_FORMAT, message_size_msg)[0]
            message = self.socket_connection_as_file.read(message_size)
            return message
        except struct.error:
            return None

    def read(self):
        counter = super(InputMessageConnector, self).MAX_READ_RETRIES
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
                super(InputMessageConnector, self).clear_socket_connection()
            else:
                if not read_buffer:
                    counter -= 1
                    super(InputMessageConnector, self).clear_socket_connection()
                else:
                    return read_buffer