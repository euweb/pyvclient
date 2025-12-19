import os
from collections import defaultdict
from xml.etree import ElementInclude
from xml.etree import ElementTree as ET

import click
import yaml


class ResourceLoader:

    def __init__(self, path):
        self.path = path

    def __call__(self, href, parse, encoding=None):

        if parse == "xml":
            with open(os.path.join(self.path, href), 'rb') as file:
                data = ET.parse(file).getroot()
        else:
            if not encoding:
                encoding = 'UTF-8'
            with open(href, 'r', encoding=encoding) as file:
                data = file.read()
        return data


def insert(target, key, *values):
    """ Inserts values to target[key]
    """

    if not (key and values):
        return target

    if key not in target:
        target[key] = []

    target[key].extend(values)
    return target


def maybe(value, callback, default=None):
    """ If value is not None, returns from calling back with that
        value; otherwise returns the default (which may also be
        callable for lazy evaluation)
    """

    if value is None:
        return default() if callable(default) else default

    return callback(value)


def get_value(value):
    """ Strip a value, or the value's text attribute,
        if either is not None
    """

    return maybe(value, lambda value: maybe(
        getattr(value, 'text', value),
        lambda value: value.strip()
    ))


def insert_info(param):
    pass


def get_enum(enum):
    return {k: v for k, v in enum.attrib.items()}


def get_unit(unit):
    unitdict = {'description': unit.attrib.get('name'),
                'type': unit.find('type').text}
    # pprint(unit)
    entity = get_value(unit.find('entity'))
    # print(entity)
    unitdict['entity'] = entity or None
    if unitdict['type'] == 'enum':
        children = list(map(get_enum, unit.findall('./enum')))
        unitdict['enum'] = children
        # if children:
        #     unitdict['enum'] = list()
        #     # dd = defaultdict(list)
        #     for child in children:
        #         ddd = {}
        #         unitdict['enum'].update(ddd.update((k, v)
        #                                            for k, v in child.attrib.items()))
        #         # dd['text'].append(child.attrib.get('text'))
        #     # d = {k: v[0] if len(v) == 1 else v
        #     #             for k, v in dd.items()}
        #     # unitdict['enum']=d
    return unitdict


def get_units(vconfigd):
    units = vconfigd.findall('.//unit')

    return {
        'units': {
            unit.find('abbrev').text: get_unit(unit)
            for unit in units
        }
    }


def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def get_device():
    return {
        'device': 'test1'
    }


def get_commands():
    return {'commands':
                'test'
            }


@click.command()
@click.argument('vcontrold_file_in', type=click.File(mode='r'))
@click.argument('pyconf_file_out', type=click.File(mode='w'))
# @click.argument('output_directory', type=click.Path(exists=True, writable=True, file_okay=False), default='.')
# @click.option('--host', '-h', default='localhost', type=str, help=u'vcontrold host')
# @click.option('--port', '-p', default=3002, type=int, help=u'vcontrold port')
# @click.option('--generate_config', '-g', default=False, is_flag=True, help=u'generates config file')
def generate_config(vcontrold_file_in, pyconf_file_out):
    """ generate configuration from vcontrold.xml file """

    xmlpath = os.path.dirname(vcontrold_file_in.name)

    vconf = ET.parse(vcontrold_file_in).getroot()

    ElementInclude.include(vconf, ResourceLoader(xmlpath))

    # print(vconf1)

    # print(ET.tostring(vconf, encoding="utf-8", method="xml").decode())

    print(yaml.dump(merge_dicts(get_device(), get_units(vconf), get_commands()), allow_unicode=True),
          file=pyconf_file_out)
    # d = etree_to_dict(vconf.find('.//units'))
    # print(yaml.dump(d))
    # print(yaml.dump(etree_to_dict(vconf.findall('.//unit'))))
    click.echo('Done!')
