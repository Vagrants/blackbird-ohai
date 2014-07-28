#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# pylint: disable=C0111,C0301,R0903,C0103,F0401

__VERSION__ = '0.1.0'

try:
    import simplejson as json
except ImportError:
    import json

import collections
import subprocess

from blackbird.plugins import base


class ConcreteJob(base.JobBase):
    """
    This class is Called by "Executor".
    Get ohai information
    and send to specified zabbix server.
    """

    def __init__(self, options, queue=None, logger=None):
        super(ConcreteJob, self).__init__(options, queue, logger)

    def build_items(self):
        """
        main loop
        """

        # ping item
        self._ping()

        # send data
        self._send_ohai()

    def build_discovery_items(self):
        """
        main loop for lld
        """

        # get ohai information
        ohai_data = self._ohai()

        item = base.DiscoveryItem(
            key='ohai.LLD',
            value=[
                {'{#OHAI_KEY}': ohai_key} for ohai_key in ohai_data
            ],
            host=self.options['hostname']
        )
        self.queue.put(item, block=False)

    def _enqueue(self, key, value):

        item = OhaiItem(
            key=key,
            value=value,
            host=self.options['hostname']
        )
        self.queue.put(item, block=False)
        self.logger.debug(
            'Inserted to queue {key}:{value}'
            ''.format(key=key, value=value)
        )

    def _ping(self):
        """
        send ping item
        """

        self._enqueue('blackbird.ohai.ping', 1)
        self._enqueue('blackbird.ohai.version', __VERSION__)

    def _flatten(self, data, parent_key='', sep='/'):
        ignore_keys = ['routes', 'arp']
        itm = []
        for k, v in data.items():
            if k in ignore_keys:
                continue
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                itm.extend(self._flatten(v, new_key).items())
            else:
                itm.append((new_key, v))
        return dict(itm)

    def _ohai(self):

        try:
            output = subprocess.Popen([self.options['path']],
                                      stdout=subprocess.PIPE).communicate()[0]

        except OSError:
            self.logger.debug(
                'can not exec "{0}", failed to get ohai information'
                ''.format(self.options['path'])
            )
            raise

        ohai_data = self._flatten(json.loads(output))
        ohai_info = dict()

        for key in ohai_data:
            if isinstance(ohai_data[key], list):
                _arr = []
                for key2 in ohai_data[key]:
                    if isinstance(key2, dict):
                        for kk, vv in key2.items():
                            ohai_info['{0}/{1}'.format(key2, kk)] = vv
                    else:
                        _arr.append(key2)

                if len(_arr) > 1:
                    ohai_info[key] = ','.join(_arr)
            else:
                ohai_info[key] = ohai_data[key]

        return ohai_info

    def _send_ohai(self):

        ohai_data = self._ohai()

        for key in ohai_data:
            item_key = 'ohai[{0}]'.format(key)
            self._enqueue(item_key, ohai_data[key])


class OhaiItem(base.ItemBase):
    """
    Enqued item.
    """

    def __init__(self, key, value, host):
        super(OhaiItem, self).__init__(key, value, host)

        self._data = {}
        self._generate()

    @property
    def data(self):
        return self._data

    def _generate(self):
        self._data['key'] = self.key
        self._data['value'] = self.value
        self._data['host'] = self.host
        self._data['clock'] = self.clock


class Validator(base.ValidatorBase):
    """
    Validate configuration.
    """

    def __init__(self):
        self.__spec = None

    @property
    def spec(self):
        """
        "user" and "password" in spec are
        for BASIC and Digest authentication.
        """
        self.__spec = (
            "[{0}]".format(__name__),
            "path=string(default='/usr/bin/ohai')",
            "hostname=string(default={0})".format(self.detect_hostname()),
        )
        return self.__spec
