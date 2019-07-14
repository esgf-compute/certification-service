from certification_service.model import get_db


def test_runs_get(app, client):
    with app.app_context():
        db = get_db()

        id = str(db.servers.find_one()['_id'])

    res = client.get('/runs/{!s}'.format(id))

    assert res.status_code == 200

    data = res.get_json()

    assert len(data) == 2

    assert data[0]['run']['state'] in ('success', 'fail')
    assert 'data' in data[0]['run']


def test_metrics_get(app, client):
    with app.app_context():
        db = get_db()

        id = str(db.servers.find_one()['_id'])

    res = client.get('/metrics/{!s}'.format(id))

    assert res.status_code == 200

    data = res.get_json()

    assert len(data) == 2

    assert data[0]['metric']['state'] in ('success', 'fail')
    assert 'data' in data[0]['metric']


def test_server_delete(app, client):
    with app.app_context():
        db = get_db()

        id = str(db.servers.find_one()['_id'])

    assert client.delete('/servers/{!s}'.format(id)).status_code == 200

    with app.app_context():
        db = get_db()

        assert db.servers.count_documents({'_id': {'$eq': id}}) == 0

        assert db.metrics.count_documents({'server_id': {'$eq': id}}) == 0

        assert db.runs.count_documents({'server_id': {'$eq': id}}) == 0


def test_server_update(app, client):
    server = client.get('/servers/').get_json()[0]

    payload = {
        'url': 'https://anewurl.com/api',
        'module': 'DASK',
        'token': 'NEW TOKEN',
    }

    res = client.put('/servers/{!s}'.format(server['id']), data=payload)

    assert res.status_code == 200

    data = res.get_json()

    assert data['url'] == payload['url']
    assert data['module'] == payload['module']
    assert data['token'] == payload['token']


def test_server_post_duplicate(client):
    server = client.get('/servers/').get_json()[0]['server']

    payload = {
        'url': server['url'],
        'module': server['module'],
        'token': server['token'],
    }

    assert client.post('/servers/', data=payload).status_code == 400


def test_server_post(client):
    payload = {
        "url": "https://testapi.com/api/",
        "module": "CDAT",
        "token": "UNIQUE_TOKEN",
    }

    res = client.post('/servers/', data=payload)

    assert res.status_code == 201

    data = res.get_json()

    assert ['url', 'module', 'token', 'date_added', 'date_updated'] == list(data.keys())


def test_server_get(client):
    res = client.get('/servers/')

    assert res.status_code == 200

    data = res.get_json()

    assert len(data) == 4
