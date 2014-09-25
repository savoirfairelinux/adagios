

import adagios
import okconfig
import pynag.Model


def fixit(nagios_cfg_file=None):
    ''' Fix the okconfig & pynag modules. For use with the tests. '''
    #
    # Not sure this is the best method but it actually works :/
    # another possibility is to copy the adagios/test/okconfig.conf to /etc/okconfig.conf

    if nagios_cfg_file is None:
        nagios_cfg_file = adagios.settings.nagios_config

    okconfig.cfg_file = nagios_cfg_file
    pynag.Model.cfg_file = nagios_cfg_file

    # For okconfig.verify()
    # because okconfig.__init__ duplicates the paths from okconfig.config in its own NS.
    # thus we have also to :
    for k, v in vars(okconfig).items():
        if (isinstance(k, str) and isinstance(v, str)
            and v.startswith('/etc/nagios/')
        ):
            print('Replacing %s with nagios3 in okconfig (%s)' % (v, okconfig.__file__))
            setattr(okconfig, k, v.replace('/etc/nagios/', '/etc/nagios3/'))

