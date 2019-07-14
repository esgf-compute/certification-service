from datetime import datetime

import bson
from pymongo.errors import DuplicateKeyError
from flask_restplus import Namespace, Resource, fields

from certification_service.model import get_db

api = Namespace('servers', description='Registered servers')

server = api.model('Server', {
    'url': fields.String(required=True),
    'module': fields.String(required=True),
    'token': fields.String(required=True),
    'date_added': fields.DateTime,
    'date_updated': fields.DateTime,
})

listed_server = api.model('ListedServer', {
    'id': fields.String(required=True),
    'server': fields.Nested(server),
})


parser = api.parser()
parser.add_argument('url', type=str)
parser.add_argument('module', type=str)
parser.add_argument('token', type=str)


@api.route('/')
class ServerList(Resource):
    @api.marshal_with(listed_server)
    def get(self):
        db = get_db()

        entries = [{'id': str(x['_id']), 'server': x} for x in db.servers.find()]

        return entries, 200

    @api.expect(server)
    @api.marshal_with(server)
    def post(self):
        db = get_db()

        args = parser.parse_args()

        now = datetime.now().isoformat()

        entry = {
            'url': args['url'],
            'module': args['module'],
            'token': args['token'],
            'date_added': now,
            'date_updated': now,

        }

        try:
            db.servers.insert_one(entry)
        except DuplicateKeyError:
            api.abort(400)

        return entry, 201


@api.route('/<string:server_id>')
class Server(Resource):
    def delete(self, server_id):
        db = get_db()

        db.servers.delete_one({'_id': bson.ObjectId(server_id)})

        db.metrics.delete_many({'server_id': bson.ObjectId(server_id)})

        db.runs.delete_many({'server_id': bson.ObjectId(server_id)})

    @api.expect(server)
    @api.marshal_with(server)
    def put(self, server_id):
        db = get_db()

        args = parser.parse_args()

        filter = {'_id': bson.ObjectId(server_id)}

        update_values = {
            'url': args['url'],
            'date_updated': datetime.now().isoformat(),
        }

        if 'module' in args:
            update_values['module'] = args['module']

        if 'token' in args:
            update_values['token'] = args['token']

        update = {'$set': update_values}

        entry = db.servers.find_one_and_update(filter, update, return_document=True)

        return entry
