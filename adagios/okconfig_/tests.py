# -*- coding: utf-8 -*-
#
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

from django.utils import unittest
from django.test.client import Client
from django.utils.translation import ugettext as _

import okconfig
import adagios.settings

okconfig.cfg_file = adagios.settings.nagios_config
from adagios.test.tools import LoadPage

#############################################################################

class TestOkconfig(LoadPage, unittest.TestCase):

    def testOkconfigVerifies(self):
        result = okconfig.verify()
        self.assertTrue(
            all(result.values()),
            'Following verifications failed:\n' + '\n'.join(
                ' -> %s : %s' % (res, isok) for res, isok in result.items() if not isok
            )
        )

    def testIndexPage(self):
        self.loadPage('/okconfig/verify_okconfig')

    def testPageLoad(self):
        """ Smoketest for the okconfig views """
        self.loadPage('/okconfig/addhost')
        self.loadPage('/okconfig/scan_network')
        self.loadPage('/okconfig/addgroup')
        self.loadPage('/okconfig/addtemplate')
        self.loadPage('/okconfig/addhost')
        self.loadPage('/okconfig/addservice')
        self.loadPage('/okconfig/install_agent')
        self.loadPage('/okconfig/edit')
        self.loadPage('/okconfig/edit/localhost')
        self.loadPage('/okconfig/verify_okconfig')


