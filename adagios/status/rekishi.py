# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Matthieu Caneill <matthieu.caneill@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import absolute_import
from collections import defaultdict, OrderedDict

import re
from urllib import quote
import logging
from adagios.status.custom_filters import ServiceStates, HostStates

logger = logging.getLogger('adagios.rekishi')

from django.utils.functional import cached_property

import adagios.settings

import rekishi.api.views.logs
import rekishi.utils.influx
from rekishi.utils.influx import decode_serie_name, query_influx


def _get_rekishi_url(base, host, service, metric, from_):
    """ Constructs an URL for Rekishi API.

    Args:
      - base (str): base URL for Graphite access
      - host (str): hostname
      - service (str): service, e.g. HTTP
      - metric (str): metric, e.g. size, time
      - from_ (str): Graphite time period

    Returns: str
    """
    host_ = _compliant_name(host)
    service_ = _compliant_name(service)
    metric_ = quote(_compliant_name(metric.replace("/", "%2F")))
    base = base.rstrip('/')
    title = adagios.settings.rekishi_title.format(**locals())

    url = "{base}/"
    if host_:
        url += "{host_}/"
        if service_:
            url += "{service_}/"
            if metric_:
                url += "{metric_}/"
        if from_:
            url += "?start=now(){from_}"

    url = url.format(**locals())
    return url


def _get_rekishi_events_url(base, host, service, from_):
    """ Constructs an URL for Rekishi API.

    Args:
      - base (str): base URL for Graphite access
      - host (str): hostname
      - service (str): service, e.g. HTTP
      - metric (str): metric, e.g. size, time
      - from_ (str): Graphite time period

    Returns: str
    """
    host_ = _compliant_name(host)
    service_ = _compliant_name(service)
    base = base.rstrip('/')
    metric = "events"
    title = adagios.settings.rekishi_title.format(**locals())

    url = "{base}/"
    if host_:
        url += "{host_}/"
        if service_:
            url += "{service_}/"
        url += "?events=true"
        if from_:
            url += "&start=now(){from_}"

    url = url.format(**locals())
    return url


def _compliant_name(name):
    """ Makes the necessary replacements for Graphite. """
    if name == '_HOST_':
        return '_self_'
    # name = ILLEGAL_CHAR.sub('_', name)
    return name


def get(base, host, service=None, metrics=None, periods=None):
    """ Returns a data structure containg URLs for Graphite.

    The structure looks like:
    [{'name': 'One day',
      'css_id' : 'day',
      'metrics': {'size': 'http://url-of-size-metric',
                  'time': 'http://url-of-time-metric'}
     },
     {...}]

    Args:
      - base (str): base URL for Graphite access
      - host (str): hostname
      - service (str): service, e.g. HTTP
      - metrics (list): list of metrics, e.g. ["size", "time"]
      - units (list): a list of <name,css_id,unit>,
        see adagios.settings.GRAPHITE_PERIODS

    Returns: list
    """
    graphs = []

    multis = {"s": 1,
              "m": 60,
              "h": 60 * 60,
              "d": 60 * 60 * 24,
              "w": 60 * 60 * 24 * 7,
              }

    def add_period_in_sec(period):
        p = {}
        p["name"] = period[0]
        p["css_id"] = period[1]
        p["period_str"] = period[2]
        try:
            integer, multi = re.search("([-0-9]*)([A-Za-z]*)", period[2]).groups()
            p["period_sec"] = int(integer) * multis[multi]
        except Exception as exp:
            pass
        return p

    periods = map(add_period_in_sec, periods)

    period = "%ds" % min([p["period_sec"] for p in  periods])

    m = {}
    for metric in metrics:
        m[metric] = _get_rekishi_url(base, host, service, metric, period)
    graphs.append(m)

    reki = {}
    reki['events_url'] = _get_rekishi_events_url(base, host, service, period)
    reki['graphs'] = graphs
    reki['periods'] = periods
    reki['host'] = _compliant_name(host)
    if service:
        reki['service'] = _compliant_name(service)

    return reki




def get_logs2(base_kw, query_kw, get_events=False):
    series = query_influx(base_kw, query_kw, get_events=get_events)
    # influxdb results is a list of "serie" where each serie contains a list of "points"
    # but adagios wants only a list of "points",
    # so let's put that in a big list (ret):
    # adagios also want it sorted by time descending :
    return sorted(
        (
            AdagiosInfluxDbSeriePoint(serie, point, idx)
            for serie in series
                for idx, point in enumerate(serie['points'])
        ),
        key=lambda pt: -pt['time']  # adagios also expects the resulting list to be time sorted.
    )



def get_logs(request, host=None, service=None, start_time=None, end_time=None):
    '''
    Get the logs from rekishi underlying influxdb ..
    :type request: django.core.handlers.wsgi.WSGIRequest
    :return: An AdagiosInfluxDbListSeries instance.
    '''

    base_kw = OrderedDict()
    if host is None:
        host = '.*'
    base_kw['host'] = host
    if service is None:
        service = '.*'
    base_kw['service'] = service

    query_kw = {}

    for k, v in request.GET.items():
        if k == 'start_time':
            query_kw['start'] = '%ss' % v
        elif k == 'end_time':
            query_kw['end'] = '%ss' % v

    if start_time is not None:
        query_kw['start'] = start_time
    if end_time is not None:
        query_kw['end'] = end_time

    get_events = 'true' == request.GET.get('events', '').lower()

    return get_logs2(base_kw, query_kw, get_events=get_events)


class AdagiosInfluxDbSeriePoint(object):
    ''' For adagios special needs.
    This class is a wrapper around a rekishi influxdb serie point values.
    You can use it a dict to directly access :
     the related :
        host_name
        service_description
        state
        time of the "point"
        ..
    '''
    def __init__(self, orig_influx_serie, orig_influx_point, point_idx):
        self._influx_serie = orig_influx_serie
        self._influx_point = orig_influx_point
        self._point_idx = point_idx
        self._supplementary_items = {}
        self._name_parts = None

    _special_values = (
        'host_name', 'service_description',
        'class_name', 'class', 'type', 'time', 'state', 'state_type',
        'output', 'text', 'options' , 'message',
    )

    _adagios_key_2_influx_key = {
        'text': 'output',
        'options': 'output',
        'message':  'output',
    }
    _influx_class_2_adagios_class = {
        'ALERT':    'alerts',
        'FLAPPING': 'flapping',
        'NOTIFICATION': 'notification',
    }

    _influx_service_state_2_adagios_state = defaultdict(
        lambda: 3, ( (v, idx) for idx, v in enumerate(ServiceStates.bool_names) ))

    _influx_host_state_2_adagios_state = defaultdict(
        lambda: 3, ( (v, idx) for idx, v in enumerate(HostStates.bool_names) ))

    def _make_column_index(attr):
        def column(self):
            return self._influx_serie['columns'].index(attr)
        column.__name__ = '%s_column' % attr
        return column
    for attr in ('time', 'state', 'state_type', 'output'):
        locals()['%s_column' % attr] = cached_property(_make_column_index(attr))

    def _get(self, orig_key, **kw):
        has_default = 'default' in kw
        default = kw.pop('default', None)

        key = self._adagios_key_2_influx_key.get(orig_key, orig_key)

        name_parts = self._name_parts
        if name_parts is None:
            name_parts = decode_serie_name(self._influx_serie['name'])
            self._name_parts = name_parts # save it for futur references
            self.host_name = name_parts[0]
            self.service_description = name_parts[1]

        is_host = self.service_description == '_self_'

        if key in ('time', 'state', 'state_type', 'output'):
            res = self._influx_point[getattr(self, '%s_column' % key)]
            if key == 'state':
                res = ( self._influx_host_state_2_adagios_state if is_host else
                        self._influx_service_state_2_adagios_state)[res]
            return res

        if key == 'type':
            return 'HOST ALERT' if is_host else 'SERVICE ALERT'
        elif key == 'class_name':
            return self._influx_class_2_adagios_class.get(name_parts[-1],
                                                          default if has_default else 'unclassified')
        elif key == 'host_name':
            return self.host_name
        elif key == 'service_description':
            return (default if has_default else '') if is_host else self.service_description
        elif key == 'duration': # for snippets_log()
            if not self._point_idx: # we are the first point of the serie, so hard to tell a duration vs the previous point..
                return 0
            prev_point = self._influx_serie['points'][self._point_idx - 1]
            return abs( self['time'] - prev_point[self.time_column] )

        logger.warning('Unhandled special value: %r', key)
        return key

    def __getitem__(self, item):
        if item in self._supplementary_items:
            return self._supplementary_items[item]
        return self._get(item)

    def __setitem__(self, key, value):
        self._supplementary_items[key] = value

    def get(self, key, default=None):
        if key in self._supplementary_items:
            return self._supplementary_items[key]
        return self._get(key, default=default)
