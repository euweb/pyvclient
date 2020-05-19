import os
from signal import pause

import click
import yaml
from pyvclient.pyvclient import PyVClient
from pyvclient.logging import setup_logging
from pyvclient.vcomm.vcomm import VComm


def get_config_form_file(filename='config.yaml'):
    if not os.path.isfile(filename):
        raise ValueError('Config file %r does not exist!' % filename)
    with open(filename, 'r') as f:
        return yaml.safe_load(f.read())


@click.command()
@click.option('--host', '-h', default='localhost',
              type=str, help=u'vcontrold host')
@click.option('--port', '-p', default=3002, type=int, help=u'vcontrold port')
@click.option('--log', '-l', type=str, help=u'log config')
@click.argument('config', type=click.Path(exists=True))
def main(host, port, config, log):
    setup_logging(log)

    config = get_config_form_file(config)

    vcomm = VComm(host=host or config['host'],
                  port=port or config['port'])
    pyvclient = PyVClient(vcomm, config)
    pyvclient.setup_timers()

    pause()

    # except (KeyboardInterrupt, SystemExit):
    #    print("Quitting.")
