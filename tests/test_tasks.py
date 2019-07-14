from unittest import mock

from certification_service import tasks


def test_pull_server_metrics():
    url = 'https://testserver.com/api/'
    module = 'CDAT'
    token = 'TOKEN'

    tasks.pull_server_metrics(url, module, token)
