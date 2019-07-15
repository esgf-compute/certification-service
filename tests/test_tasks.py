from unittest import mock

import json

from certification_service import tasks
from certification_service.model import get_db


def test_store_run_results(app, mocker):
    with app.app_context():
        db = get_db()

        server = db.servers.find_one()

        db.runs = mock.MagicMock()

        tasks.store_run_results(db, server['url'], 'data', state='success')

        db.runs.insert_one.assert_called_with({
            'data': 'data',
            'server_id': server['_id'],
            'date_added': db.runs.insert_one.call_args[0][0]['date_added'],
            'state': 'success'
        })


def test_store_metrics_results(app, mocker):
    with app.app_context():
        db = get_db()

        server = db.servers.find_one()

        db.metrics = mock.MagicMock()

        tasks.store_metrics_results(db, server['url'], 'data', state='success')

        db.metrics.insert_one.assert_called_with({
            'data': 'data',
            'server_id': server['_id'],
            'date_added': db.metrics.insert_one.call_args[0][0]['date_added'],
            'state': 'success'
        })


def test_run_certification_exception(app, mocker):
    with app.app_context():
        server = get_db().servers.find_one()

    certification = mocker.patch('certification_service.tasks.run_server_certification.apply_async')

    def apply_async(*args, **kwargs):
        if args[0][0] == server['url']:
            raise Exception('error')

    certification.side_effect = apply_async

    store = mocker.patch('certification_service.tasks.store_run_results')

    tasks.run_certification()

    with app.app_context():
        store.assert_called_with(get_db(), server['url'], 'error', state='fail')


def test_run_certification(app, mocker):
    certification = mocker.patch('certification_service.tasks.run_server_certification.apply_async')

    tasks.run_certification()

    assert certification.call_count == 4


def test_run_server_certification_exception(app, mocker):
    with app.app_context():
        server = get_db().servers.find_one()

    def new_main(*args, **kwargs):
        raise Exception('error')

    mocker.patch('certification_service.tasks.main', new=new_main)

    store = mocker.patch('certification_service.tasks.store_run_results')

    tasks.run_server_certification(server['url'], 'CDAT', 'TOKEN')

    with app.app_context():
        store.assert_called_with(get_db(), server['url'], 'error', state='fail')


def test_run_server_certification(app, mocker):
    with app.app_context():
        server = get_db().servers.find_one()

    def new_main(*args, **kwargs):
        with open(args[-1], 'w') as outfile:
            outfile.write('hello')

    mocker.patch('certification_service.tasks.main', new=new_main)

    store = mocker.patch('certification_service.tasks.store_run_results')

    tasks.run_server_certification(server['url'], 'CDAT', 'TOKEN')

    with app.app_context():
        store.assert_called_with(get_db(), server['url'], 'hello', state='success')


def test_pull_metrics_exception(app, mocker):
    with app.app_context():
        server = get_db().servers.find().next()

    apply_async = mocker.patch('certification_service.tasks.pull_server_metrics.apply_async')

    def apply_async_ret(*args, **kwargs):
        if args[0][0] == server['url']:
            raise Exception()

    apply_async.side_effect = apply_async_ret

    store = mocker.patch('certification_service.tasks.store_metrics_results')

    tasks.pull_metrics()

    with app.app_context():
        store.assert_called_with(get_db(), server['url'], '', state='fail')


def test_pull_metrics(app, mocker):
    task = mocker.patch('certification_service.tasks.pull_server_metrics')

    tasks.pull_metrics()

    assert task.apply_async.call_count == 4


def test_pull_server_metrics_exception(app, mocker):
    with app.app_context():
        server = get_db().servers.find_one()

    module = 'CDAT'
    token = 'TOKEN'

    client = mocker.patch('certification_service.tasks.cwt.WPSClient')

    client.return_value.execute.side_effect = Exception('error')

    store = mocker.patch('certification_service.tasks.store_metrics_results')

    db = mocker.patch('certification_service.tasks.get_db')

    tasks.pull_server_metrics(server['url'], module, token)

    db_call = db.return_value.__enter__.return_value

    store.assert_called_with(db_call, server['url'], str(Exception('error')), state='fail')


def test_pull_server_metrics(app, mocker):
    with app.app_context():
        server = get_db().servers.find_one()

    module = 'CDAT'
    token = 'TOKEN'

    client = mocker.patch('certification_service.tasks.cwt.WPSClient')

    output = {'url': 'https://examplesite.com/api/'}

    client.return_value.process_by_name.return_value.output = output

    store = mocker.patch('certification_service.tasks.store_metrics_results')

    db = mocker.patch('certification_service.tasks.get_db')

    tasks.pull_server_metrics(server['url'], module, token)

    db_call = db.return_value.__enter__.return_value

    store.assert_called_with(db_call, server['url'], json.dumps(output), state='success')
