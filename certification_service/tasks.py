import json
import os
from datetime import datetime

import cwt
import pymongo
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

db = client['certification']

servers = db['servers']

metrics_col = db['metrics']

os.environ['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/0'

app = Celery(__name__)

app.conf.timezone = 'America/Los_Angeles'

app.conf.beat_schedule = {
    'test': {
        'task': 'certification_service.tasks.pull_metrics',
        'schedule': crontab(),
    }
}

logger = get_task_logger(__name__)


@app.task(bind=True)
def pull_metrics(self):
    api_key = 'A9IqTvcNDeLfpbpeThihIykXbFzP15QDdGtXH0lVmDmnFHNx8mLNlmPmNrzNI2mG'

    client = cwt.WPSClient('https://aims2.llnl.gov/wps/', api_key=api_key)

    metrics = client.process_by_name('CDAT.metrics')

    client.execute(metrics)

    metrics.wait()

    server = servers.find_one({'url': 'https://aims2.llnl.gov/wps/'})

    entry = {
        'server_id': server['_id'],
        'created': datetime.now(),
        'data': json.dumps(metrics.output),
    }

    metrics_col.insert_one(entry)

    return metrics.output
