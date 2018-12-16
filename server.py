# Tooling
from gentools import load_ini as GENTOOLS_loadini
from gentools import initialize as GENTOOLS_initialize
from gentools import Logger as GENTOOLS_Logger
from gentools import Socket as GENTOOLS_Socket

from gentools import DataContainer as GENTOOLS_DataCont

from time import sleep as TimeSleep

# Threading
from threading import Thread as threThread


class ServerClient(threThread):
    def __init__(self, in_addr, in_port, master_logger, size, connection):
        """
            in_addr: str
            in_port: int
            master_logger: Logger
        """
        threThread.__init__(self)

        # Logging and signaling
        self.logger = master_logger
        self.desc = "CLIENT-%s:%s " % (in_addr, in_port)
        self.signal = True
        
        # Client specifics
        self.addr = in_addr
        self.port = in_port
        self.size = size
        self.connection = connection

        # Data itself
        self.data_cont = GENTOOLS_DataCont()

    def run(self):
        self.logger.debug(self.desc + "starting message handling")
        while self.signal:
            # Receive the payload
            self.logger.debug(self.desc + "receiving payload")
            self.data_cont._decode(self.connection.recv(self.size).decode())

            self.logger.debug(self.desc + 'waiting for data to be processed')
            while not self.data_cont._ready:
                TimeSleep(1)
            # try to send data back
            try:
                self.connection.send(self.data_cont._payload.encode())
                self.logger.debug(self.desc + "successfully sent back to %s:%s" % (self.addr, self.port))
                self.connection.close()
                self.signal = False
            except Exception as e:
                self.logger.error(self.desc + "FAILED to send: %s" % str(e))

## 
# Server itself
class Server(threThread):
    def __init__(self):
        """
            General usage server
        """
        # Threading, to not block terminals
        threThread.__init__(self)
        
        # Logging
        self.desc = "SERVER: "
        self.logger = GENTOOLS_Logger

        # Connection
        self.socket = GENTOOLS_Socket
        self.server = True

        # Clients index
        self.clients = {}

        # Garbage collector process
        self.garbage_thread = None
        

    ## General connection tools
    def run(self):
        self.logger.debug(self.desc + "starting garbage collecting processor")
        self.garbage_thread = threThread(target = self.garbage_collector)
        self.garbage_thread.start()

        while True:
            self.logger.info(self.desc + 'waiting for connection')
            # accept the connection
            client, addr = self.socket.socket.accept()
            self.logger.debug(self.desc + "incoming data from: %s:%s" % addr)

            # create new client payload, if not exists
            # 'instance syntax':
            # str(ip_address:port)
            client_id = "%s:%s" % (addr)
            if self.clients.get(client_id) is None:
                self.clients[client_id] = ServerClient(addr[0], addr[1], self.logger, self.socket.size, client)
                self.clients[client_id].start()

    # Garbage collector
    def garbage_collector(self):
        while True:
            TimeSleep(1)
            if len(self.clients) == 0:
                continue

            clients_copy = dict(self.clients)

            for item in clients_copy.keys():
                if not clients_copy[item].signal:
                    self.logger.debug(self.desc + "cleaning inactive client %s" % item)
                    del self.clients[item]

    def _initialize(self, in_ini = 'config.ini'):
        GENTOOLS_initialize(self, ['logger', 'socket'], in_ini)