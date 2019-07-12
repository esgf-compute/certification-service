import json
import os
import tempfile
from datetime import datetime
from datetime import timedelta
from uuid import uuid4

import cwt
import pymongo
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from cwt_cert import main

from certification_service.service import SUCCESS
from certification_service.service import FAIL

os.environ['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/0'

DEV = os.environ.get('DEV', False)

app = Celery(__name__)

app.conf.timezone = 'America/Los_Angeles'

app.conf.beat_schedule = {
    'pull_metrics': {
        'task': 'certification_service.tasks.pull_metrics',
        # 8 am each day
        'schedule': crontab(minute='0', hour='8'),
        'options': {
            'ignore_result': True,
        }
    },
    'run_certification': {
        'task': 'certification_service.tasks.run_certification',
        # 1 st of every month
        'schedule': crontab(minute='0', hour='0', day_of_month='1'),
        'options': {
            'ignore_result': True,
        },
    },
    'remove_old_metrics': {
        'task': 'certification_service.tasks.remove_old_metrics',
        # 1 am each day
        'schedule': crontab(minute='0', hour='1'),
        'options': {
            'ignore_result': True,
        },
    },
}

if DEV:
    app.conf.beat_schedule['pull_metrics']['schedule'] = crontab(minute='*/1')

    app.conf.beat_schedule['run_certification']['schedule'] = crontab(minute='*/5')

    app.conf.beat_schedule['remove_old_metrics']['schedule'] = crontab(minute='*/4')

logger = get_task_logger(__name__)


def store_run_results(db, url, data, **result):
    server = db.servers.find_one({'url': url})

    result.update({
        'server_id': server['_id'],
        'data': data,
        'date_added': datetime.now().isoformat(),
    })

    db.runs.insert_one(result)


def store_metrics_results(db, url, data, **result):
    server = db.servers.find_one({'url': url})

    result.update({
        'server_id': server['_id'],
        'data': data,
        'date_added': datetime.now().isoformat(),
    })

    db.metrics.insert_one(result)


@app.task(bind=True)
def remove_old_metrics(self):
    try:
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

        db = client['certification']

        cutoff = datetime.now() - timedelta(182)

        # Remove all metrics older than 6 months (182 days)
        db.metrics.delete_many({'date_added': {'$gte': cutoff}})
    finally:
        client.close()


@app.task(bind=True)
def run_certification(self):
    try:
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

        db = client['certification']

        for server in db.servers.find():
            args = (server['url'], server['module'], server['token'])

            try:
                run_server_certification.apply_async(args, ignore_result=True)
            except Exception as e:
                logger.error('Error starting certification task for %r', server['url'])

                store_run_results(db, server['url'], str(e), state=FAIL)

                pass

        logger.info('Finished creating metrics tasks')
    finally:
        client.close()


@app.task(bind=True)
def run_server_certification(self, url, module, token):
    try:
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

        db = client['certification']

        with tempfile.TemporaryDirectory() as temp_dir:
            uid = str(uuid4())[:8]

            temp_file = os.path.join(temp_dir, '{!s}.json'.format(uid))

            args = [
                '--url', url,
                '--module', module,
                '--token', token,
                '-m', 'server and not stress',
                '--json-report-file', temp_file,
            ]

            main(*args, skip_exit=True)

            with open(temp_file) as infile:
                data = infile.read()
    except Exception as e:
        store_run_results(db, url, str(e), state=FAIL)

        pass
    else:
        store_run_results(db, url, data, state=SUCCESS)
    finally:
        client.close()


@app.task(bind=True)
def pull_metrics(self):
    try:
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

        db = client['certification']

        for server in db.servers.find():
            args = (server['url'], server['module'], server['token'])

            try:
                pull_server_metrics.apply_async(args, ignore_result=True)
            except Exception as e:
                logger.error('Error starting metrics task for %r', server['url'])

                store_metrics_results(db, server['url'], str(e), state=FAIL)

                pass

        logger.info('Finished creating metrics tasks')
    finally:
        client.close()


@app.task(bind=True)
def pull_server_metrics(self, url, module, token):
    try:
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

        db = client['certification']

        wps_client = cwt.WPSClient(url, api_key=token)

        logger.info('Connecting to client %r', url)

        process = wps_client.process_by_name('{!s}.metrics'.format(module))

        logger.info('Found operation %r', process.identifier)

        wps_client.execute(process)

        logger.info('Executing operation, waiting 16 seconds for results')

        process.wait(16)
    except Exception as e:
        store_metrics_results(db, url, str(e), state=FAIL)

        pass
    else:
        store_metrics_results(db, url, json.dumps(process.output), state=SUCCESS)
    finally:
        client.close()
