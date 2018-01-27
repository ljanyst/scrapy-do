#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   22.01.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import requests
import urllib3

from scrapy_do.client import ClientException
from requests.auth import HTTPDigestAuth


#-------------------------------------------------------------------------------
def request(method, url, payload={}, auth=None, ssl_verify=True):
    """
    Send a request to the server and retrieva the response.

    :param method:                            request method ('POST' or 'GET')
    :param url:                               url to be queried
    :param payload:                           parameters of the request
    :param auth:                              tuple containing the authorization
                                              information
    :param ssl_verify:                        SSL verification flag
    :raises scrapy_do.client.ClientException: an error
    :return:                                  parsed JSON response of the server
                                              or raw data
    """
    assert method == 'POST' or method == 'GET'

    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if auth is not None:
        auth = HTTPDigestAuth(*auth)

    try:
        if method == 'POST':
            r = requests.post(url, data=payload, auth=auth, verify=ssl_verify)
        else:
            r = requests.get(url, params=payload, auth=auth, verify=ssl_verify)
    except Exception as e:
        raise ClientException(str(e))

    if r.headers['Content-Type'] == 'application/json':
        data = r.json()
    else:
        data = r.text

    if r.status_code != 200:
        if r.headers['Content-Type'] == 'application/json':
            raise ClientException(data['msg'])
        else:
            raise ClientException(data)
    return data
