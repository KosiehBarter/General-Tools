# Config parser
from configparser import ConfigParser as cp_CP

# Logging
from logging import getLogger as LOGGL
from logging import Handler as LOGH

from logging import CRITICAL as logCRIT
from logging import ERROR as logERR
from logging import WARNING as logWARN
from logging import INFO as logINFO
from logging import DEBUG as logDEBUG
from logging import NOTSET as logNOTSET

# System standard out
from sys import stdout as SYSSTDOUT

# Sockets
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from socket import socket as SoSocket

# JSON
from json import loads as JSLoads
from json import dumps as JSDumps


# Main load ini
def load_ini(in_ini, section = None):
    config = cp_CP()
    config.read(in_ini)
    ret_dict = {}

    if section is None:
        pass
    # Loop through all elements in section
    for item in dict(config.items(section)):
        ret_dict[item] = config[section][item]
    
    # Return the dictionary with results
    return ret_dict

# Main initialize
def initialize(in_obj, init_list, inifile='config.ini'):
    for initobj in init_list:
        setattr(in_obj, initobj, getattr(in_obj, initobj)() ) # internal parentheses are calling the object.
        
        # pre-Initialize the object, mainly for non-logger
        if hasattr(getattr(in_obj, initobj), '_pre_initialize'):
            getattr(in_obj, initobj)._pre_initialize(in_obj.logger)

        # Socket-only, if server
        if hasattr(getattr(in_obj, initobj), 'server') and hasattr(in_obj, 'server'):
            getattr(in_obj, initobj).server = getattr(in_obj, 'server')

        # normally, initialize it
        getattr(in_obj, initobj)._initialize(inifile)
        
        # get object's status
        obj_status = getattr(in_obj, initobj).status
        
        # get directly objects, if possible
        if hasattr(getattr(in_obj, initobj), '_get_main'):
            setattr(in_obj, initobj, getattr(in_obj, initobj)._get_main())

        # Log it.
        if obj_status:
            if hasattr(getattr(in_obj, initobj), 'desc'):
                description = getattr(in_obj, initobj).desc.replace(':', '')
            else:
                description = initobj
            in_obj.logger.info(in_obj.desc + "initialized: %s" % description)

        else:
            in_obj.logger.critical(in_obj.desc + "FAILED to initialize: %s: %s" % (getattr(in_obj, initobj).desc, getattr(in_obj, initobj).error))


class DataContainer(object):
    """
        Data container 
    """
    def __init__(self):
        self._ready = False

        self._attr_list = []
        self._payload = ''

    def _decode(self, in_json):
        tmp_data = JSLoads(in_json)
        for key in tmp_data.keys():
            setattr(self, key, tmp_data.get(key))
            self._attr_list.append(key)
    
    def _encode(self):
        tmp_dict = dict()
        for attr in dir(self):
            if not attr[0] == '_':
                tmp_dict[attr] = getattr(self, attr)
                delattr(self, attr)
        
        self._attr_list = []
        self._payload = JSDumps(tmp_dict)
        del tmp_dict
        # make the datacontainer ready
        self._ready = True

# General Logging Daemon for almost everything
class SystemdHandler(LOGH):
    PREFIX = {
        # EMERG <0>
        # ALERT <1>
        logCRIT: "<2>",
        logERR: "<3>",
        logWARN: "<4>",
        # NOTICE <5>
        logINFO: "<6>",
        logDEBUG: "<7>",
        logNOTSET: "<7>"
    }

    def __init__(self, stream = SYSSTDOUT):
        self.stream = stream
        LOGH.__init__(self)

    def emit(self, record):
        try:
            mesg = self.PREFIX[record.levelno] + self.format(record) + "\n"
            self.stream.write(mesg)
            self.stream.flush()
        except Exception:
            self.handleError(record)


class Logger(object):
    def __init__(self):
        self.logger = LOGGL()
        self.status = False
        self.desc = "Logger"

    def _initialize(self, in_ini = 'config.ini'):
        loglevel = load_ini(in_ini, 'LOGGING')
        self.logger.setLevel(loglevel['level'])
        self.logger.addHandler(SystemdHandler())
        self.status = True

    def _get_main(self):
        return self.logger


# SOCKET for general usage
class Socket(object):
    def __init__(self):
        # Logging
        self.logger = None
        self.desc = "SOCK_COMM: "
        self.status = False

        # socket related
        self.socket = None
        self.size = None
        self.server = False

    def _pre_initialize(self, master_logger):
        self.logger = master_logger

    def _initialize(self, in_ini = 'config.ini'):
        self.logger.info(self.desc + 'starting initialization')
        if self.size is None:
            data_dict = load_ini(in_ini, 'SOCKET')
            self.size = int(data_dict['size'])

        # Server-only
        if self.server:
            self.socket = SoSocket(AF_INET, SOCK_STREAM)
            try:
                self.logger.info(self.desc + 'starting server socket')
                data_dict = load_ini(in_ini, 'SERVER')
                self.socket.bind((data_dict['host'], int(data_dict['port'])))
                self.socket.listen(int(data_dict['max_clients']))
                self.logger.info(self.desc + 'started server socket successfully')
                self.status = True
            except Exception as e:
                self.logger.error(self.desc + "FAILED to open, because: %s" % str(e))
                self.error = str(e)
                self.socket.close()
        # Client only, supports reinitialize
        else:
            self.logger.info(self.desc + "starting client socket")
            if not hasattr(self, 'server') and not hasattr(self, 'port') or type(self.server) == bool:
                data_dict = load_ini(in_ini, 'CLIENT')
                setattr(self, 'server', data_dict['server'])
                setattr(self, 'port', int(data_dict['port']))
            self.status = True

    # Client-only!
    def exchange(self, in_data, wait = False):
        self.socket = SoSocket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            self.socket.connect((self.server, self.port))
            self.socket.sendall(in_data.encode())
        except Exception as e:
            self.logger.error(self.desc + "FAILED: %s" % str(e))
        # reply data
        if wait:
            reply = self.socket.recv(self.size).decode()
        else:
            reply = None
        self.socket.close()

        if reply == '':
            self.logger.debug(self.desc + 'client received no data.')
        elif reply is None:
            pass
        else:
            return reply