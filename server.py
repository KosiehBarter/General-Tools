from socket import socket as SSock
from socket import AF_INET as S_AF_INET
from socket import SOCK_STREAM as S_SOCK_STREAM

# Tooling
from gentools import load_ini as GENTOOLS_loadini
from gentools import initialize as GENTOOLS_initialize
from gentools import Logger as GENTOOLS_Logger
from gentools import Socket as GENTOOLS_Socket

class Playground(object):
    def __init__(self):
        """
            
        """
        self.width = 0
        self.height = 0

        # Logging
        self.desc = "NetoSweeper SERVER: "
        self.logger = GENTOOLS_Logger

        # Connection
        self.socket = GENTOOLS_Socket
        self.max_clients = None

        # Signaling
        self.signal = True


    def run(self):
        while self.signal:
            client, addr = self.socket.socket.accept()
            data = client.recv(self.socket.size)
            self.logger.debug(self.desc + "incoming: %s, data: %s" % (addr, data.decode()))
            client.close()


    def _initialize(self, in_ini = 'config.ini'):
        GENTOOLS_initialize(self, ['logger', 'socket'], in_ini)