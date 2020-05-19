=========
pyvclient
=========

A python module providing a homie convention mqtt interface to communicate with viessmann heater accessed by vcontrold.

Usage
=====

    - Create a virtual environment

        python -m venv .venv
        . .venv/bin/activate
        # fish users: . .venv/bin/activate.fish

    - Install package (plus dev dependencies) in the virtual environment

        pip install .

    - Run as a console script

        pyvclient --log src/conf/logging.yaml src/conf/config.yaml

Links
=====
https://github.com/openv/openv/wiki/vcontrold
https://homieiot.github.io/

Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
