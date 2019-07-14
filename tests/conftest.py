import pytest

from certification_service import create_app
from certification_service.model import get_client
from certification_service.model import get_db
from certification_service.model import init_db


def load_fake_data(db):
    servers = db.servers.insert_many([
        {
            'url': 'http://site{!s}.com/api'.format(x),
            'module': 'CDAT{!s}'.format(x),
            'token': 'TOKEN{!s}'.format(x),
        }
        for x in range(4)
    ])

    db.metrics.insert_many([
        {
            'state': 'success' if y == 0 else 'fail',
            'data': 'random data stuff',
            'server_id': x,
        }
        for x in servers.inserted_ids for y in range(2)
    ])

    db.runs.insert_many([
        {
            'state': 'success' if y == 0 else 'fail',
            'data': 'random data stuff',
            'server_id': x,
        }
        for x in servers.inserted_ids for y in range(2)
    ])


@pytest.fixture
def app():
    app = create_app()

    with app.app_context():
        get_client().drop_database('certification')

        init_db()

        load_fake_data(get_db())

    yield app


@pytest.fixture
def client(app):
    return app.test_client()
