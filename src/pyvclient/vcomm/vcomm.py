import logging
import telnetlib
import threading
import time

logger = logging.getLogger(__name__)

class VCommError(Exception):
    pass


class VComm():
    _has_lock = False

    def __init__(self, host='127.0.0.1', port=3002):
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self._connection_errorlog = 5
        self._connection_attempts = 0
        self._has_lock = False

    def __connect(self):
        logger.info("connect to vcontrold")
        if self.__connected():
            return
        try:
            logger.debug('create new connection to %s',
                              self.host)
            self.tn = telnetlib.Telnet(self.host, self.port)
            self.tn.read_until(b"vctrld>")
        except Exception as e:
            logger.error(e)

    
    def __connected(self):
        # see: https://stackoverflow.com/questions/8480766/detect-a-closed-connection-in-pythons-telnetlib/42124099
        if self.tn.get_socket().fileno() == -1:
            return False
        else:
            return True

    def __close(self):
        logger.info("disconnect from vcontrold")
        try:
            self.tn.write(b"quit\n")
            self.tn.close()
        except Exception as e:
            logger.error(e)
        finally:
            # TODO fix hack due to reconnection errors
            time.sleep(1)
    
    def __cleanup(self):
        if self._has_lock:
            self.__close()
            self._lock.release()
            self._has_lock = False

    def __request(self, cmd):

        logger.debug("command: %s", cmd)

        attempts = 5

        value = None

        while not value:

            if not self.__connected():
                self.__connect()

            try:
                self.tn.write(cmd.encode('utf-8') + b"\n")
                value = self.tn.read_until(
                    b'vctrld>'
                ).decode('utf-8').splitlines()[:-1]
                logger.debug("received value: " + str(value))
                if (value[0] == 'ERR: <RECV: read error 11'):
                    logger.error('viessmann: received error for %s', cmd)
                    value = None
            except Exception as e:
                logger.error(e)
                attempts -= 1
                if attempts < 0:
                    self.__cleanup()
                    raise VCommError("No connection to vcontrold.")

        return value

    def set_command(self, reg, value):
        logger.debug("set  %s to %s", reg, value)
        self._lock.acquire()
        self._has_lock = True

        attempt = 5
        success = False

        cmd = 'set' + reg + " " + value + "\n"

        if not self.__connected():
            self.__connect()

        while not success & attempt > 0:
            try:
                logger.debug("set: [" + cmd + "]")
                self.tn.write(cmd.encode('utf-8'))
                value = self.tn.read_until(b'vctrld>').decode('utf-8').splitlines()[:-1]
                logger.debug("received feedback: " + str(value))
                if str(value) == "['OK']":
                    success = True
                attempt -= 1
            except Exception as e:
                logger.error(e)
                attempt -= 1
                if attempt < 0:
                    self.__cleanup()
                    raise VCommError("No connection to vcontrold possible")
            finally:
                self.__cleanup()
        return success

    def process_commands(self, commands):
        logger.info("process commands")
        logger.debug(commands)
        self._lock.acquire()
        self._has_lock = True
        ret = {}
        try:
            for cmd in commands:
                ret.update({cmd: self.__request(cmd)})
        finally:
            self.__cleanup()

        return ret

    def process_command(self, cmd):
        return process_command([cmd])

    def get_commands(self):
        return self.process_command('commands')

    def get_device(self):
        return self.process_command('device')
