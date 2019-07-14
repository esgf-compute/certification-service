import pymongo
from pymongo.errors import DuplicateKeyError
from flask import current_app
from flask import g


def get_client():
    if 'client' not in g:
        g.client = pymongo.MongoClient(current_app.config['DATABASE'])

    return g.client


def get_db():
    return get_client().certification


def init_db():
    db = get_db()

    try:
        db.servers.create_index('url', unique=True)
    except DuplicateKeyError:
        pass


def close_db(e=None):
    db_client = g.pop('db_client', None)

    if db_client is not None:
        db_client.close()


def init_app(app):
    app.teardown_appcontext(close_db)
