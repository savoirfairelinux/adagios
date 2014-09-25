# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

import json

from django.utils import unittest
from django.test.client import Client

from adagios.test.tools import LoadPage


class LiveStatusTestCase(LoadPage, unittest.TestCase):
    def testPageLoad(self):
        """ Smoke Test for various rest modules """
        self.loadPage('/rest')
        self.loadPage('/rest/status/')
        self.loadPage('/rest/pynag/')
        self.loadPage('/rest/adagios/')
        self.loadPage('/rest/status.js')
        self.loadPage('/rest/pynag.js')
        self.loadPage('/rest/adagios.js')

    def testDnsLookup(self):
        """ Test the DNS lookup rest call """
        path = "/rest/pynag/json/dnslookup"
        rsp = self.loadPage(path, method=Client.post, data={'host_name':'localhost'})
        json_data = json.loads(rsp.content)
        self.assertIn('addresslist', json_data, "Expected 'addresslist' to appear in response")

