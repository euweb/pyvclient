import logging
import telnetlib
import threading
import time

logger = logging.getLogger(__name__)

class VCommError(Exception):
    pass


class VComm():

    def __init__(self, host='127.0.0.1', port=3002):
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self.connected = False
        self._connection_errorlog = 5
        self._connection_attempts = 0

    def __connect(self):
        logger.info("connect to vcontrold")
        if self.connected:
            return
        try:
            logger.debug('create new connection to %s',
                              self.host)
            self.tn = telnetlib.Telnet(self.host, self.port)
            self.tn.read_until(b"vctrld>")
        except Exception as e:
            self.connected = False
            logger.error(e)
        else:
            self.connected = True

    def __close(self):
        logger.info("disconnect from vcontrold")
        self.connected = False
        try:
            self.tn.write(b"quit\n")
            self.tn.close()
        except Exception as e:
            logger.error(e)
        finally:
            # TODO fix hack due to reconnection errors
            time.sleep(1)

    def __request(self, cmd):

        logger.debug("command: %s", cmd)

        attempts = 5

        value = None

        while not value:

            if not self.connected:
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
                    self._lock.release()
                    raise VCommError("No connection to vcontrold.")

        return value

    def process_commands(self, commands):
        logger.info("process commands")
        logger.debug(commands)
        self._lock.acquire()
        ret = {}
        try:
            for cmd in commands:
                ret.update({cmd: self.__request(cmd)})
        finally:
            self.__close()
            self._lock.release()

        return ret

    def process_command(self, cmd):
        return process_command([cmd])

    def get_commands(self):
        return self.process_command('commands')

    def get_device(self):
        return self.process_command('device')
