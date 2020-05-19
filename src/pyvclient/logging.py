import logging
import logging.config
import os

import coloredlogs
import yaml


def setup_logging(default_path='logging.yaml', default_level=logging.INFO):
    path = default_path

    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)
        print('Failed to load configuration file. Using default configs')
