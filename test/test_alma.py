import os
import re
from importlib import reload
import unittest

import responses
import requests

from pyalma import alma, records


def setUpModule():
    os.environ['ALMA_API_KEY'] = 'my fake key'
    os.environ['ALMA_API_REGION'] = 'APAC'
    reload(alma)


class TestAlmaSetup(unittest.TestCase):

    def test_init(self):
        api = alma.Alma(apikey='unreal', region='EU')
        self.assertEqual(api.apikey, 'unreal')
        self.assertEqual(api.endpoint, alma.ENDPOINTS['EU'])

    def test_init_errors(self):
        self.assertRaises(Exception, alma.Alma, **{'apikey':None})
        self.assertRaises(Exception, alma.Alma, **{'region':None})
        self.assertRaises(Exception, alma.Alma, **{'region': 'XX'})

    def test_init_env_vars(self):
        api = alma.Alma()
        self.assertEqual(api.apikey, 'my fake key')
        self.assertEqual(api.endpoint, alma.ENDPOINTS['APAC'])
    
    def test_baseurl(self):
        api = alma.Alma()
        url = 'https://api-ap.hosted.exlibrisgroup.com/almaws/v1/'
        self.assertEqual(api.baseurl, url)

    def test_fullurl(self):
        ids = {'mms_id': 7777777, 'holding_id': 55555, 'item_pid': 333}
        expect = 'https://api-ap.hosted.exlibrisgroup.com/almaws/v1/'
        expect += 'bibs/7777777/holdings/55555/items/333'
        url = alma.Alma().fullurl('item', ids)
        self.assertEqual(url, expect)

    def test_headers(self):
        expect = {
            'User-Agent': 'pyalma/0.1.0',
            'Authorization': 'apikey my fake key',
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
        }
        headers = alma.Alma().headers(content_type='xml')
        self.assertEqual(headers, expect)


class TestAlmaGETRequests(unittest.TestCase):

    def setUp(self):
        self.api = alma.Alma()

    def buildResponses(self):
        # bib mock response
        biburl = self.api.baseurl + r'bibs/\d+'
        bib_re = re.compile(biburl)
        with open('test/bib.dat', 'r') as f:
            responses.add(responses.GET, bib_re, 
                status=200, 
                content_type='application/json',
                body=f.read())
        # holdings mock response
        holdurl = biburl + r'/holdings/\d+'
        hold_re = re.compile(holdurl)
        with open('test/hold.dat', 'r') as f:
            responses.add(responses.GET, hold_re, 
                status=200, 
                content_type='application/json',
                body=f.read())
        # item mock response
        itemurl = holdurl + r'/items/\d+'
        item_re = re.compile(itemurl)
        with open('test/item.dat', 'r') as f:
            responses.add(responses.GET, item_re, 
                status=200, 
                content_type='application/json',
                body=f.read())

    @responses.activate
    def test_alma_request(self):
        self.buildResponses()
        resp = self.api.request('GET', 'bib', {'mms_id': 9922405930001552})
        data = resp.json()
        self.assertEqual(data['created_date'], '2013-07-14Z')

    @responses.activate
    def test_alma_bib(self):
        self.buildResponses()
        bib = self.api.bib(9922405930001552)
        self.assertIsInstance(bib, records.Bib)


if __name__ == '__main__':
    unittest.main()