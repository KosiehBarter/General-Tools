from gentools import Socket
from gentools import Logger
from gentools import initialize as GENTOOLS_initialize

class Client(object):
    """

    """
    def __init__(self):
        # Connection
        self.socket = Socket
        self.server = False

        # Logging
        self.logger = Logger
        self.desc = 'NetoSweeper CLIENT:'

    
    def _initialize(self, in_ini = 'config.ini'):
        GENTOOLS_initialize(self, ['logger', 'socket'])
