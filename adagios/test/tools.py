
import re
import html2text

from django.test.client import Client


##############################################################
# not sure it's safe to use a global one:
html2text_handle = html2text.HTML2Text()
def safe_html2text(html):
    ''' Extract the text content from an html content.
For unicode/binary data (non-ascii), try to escape them in
their hex values.
To be only used for tests / debug purposes.
    '''
    html = ( repr(html).replace(r'\n', '\n')
             if isinstance(html, type(b''))
             else html.encode('ascii', 'replace') )
    out = html2text_handle.handle(html) # this returns unicode
    out = out.encode('ascii', 'replace')
    return re.sub('\n{3,}', '\n\n',
                  re.sub('(^|\n)\s+(\n|$)', '\n', out))
##############################################################


class LoadPage(object):

    def loadPage(self, url, expected_code=200, method=Client.get, data={}):
        """ Load one specific page, and assert if return code is not 200 """
        c = Client()
        rsp = method(c, url, data=data)
        self.assertEqual(expected_code, rsp.status_code,
                         "Expected status code {expected_code} for page {url} "
                         "but got {rsp.status_code}\nCONTENT RECEIVED={content}".format(
                             expected_code=expected_code, url=url, rsp=rsp,
                             content=safe_html2text(rsp.content)
                         ))
        return rsp
