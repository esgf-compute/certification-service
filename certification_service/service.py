from datetime import datetime

import bson
import pymongo
from flask import Flask
from flask_restplus import Api, Resource, fields

# Setup mongo
client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

db = client['certification']

db.servers.create_index('url', unique=True)

# Setup Flask and Flask-restplus
app = Flask(__name__)

api = Api(app)


SUCCESS = 'success'
FAIL = 'fail'


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

metric = api.model('Metric', {
    'state': fields.String,
    'data': fields.String,
    'date_added': fields.DateTime,
})

listed_metric = api.model('ListedMetric', {
    'id': fields.String(required=True),
    'metric': fields.Nested(metric),
})

run = api.model('Run', {
    'state': fields.String,
    'data': fields.String,
    'date_added': fields.DateTime,
})

listed_run = api.model('ListedRun', {
    'id': fields.String(required=True),
    'run': fields.Nested(run),
})

parser = api.parser()
parser.add_argument('url', type=str)
parser.add_argument('module', type=str)
parser.add_argument('token', type=str)


@api.route('/server/<string:server_id>/run')
class RunList(Resource):
    @api.marshal_with(listed_run)
    def get(self, server_id):
        entries = [{'id': str(x['_id']), 'run': x} for x in db.runs.find({'server_id': bson.ObjectId(server_id)})]

        return entries, 200


@api.route('/servers')
class ServerList(Resource):
    @api.marshal_with(listed_server)
    def get(self):
        entries = [{'id': str(x['_id']), 'server': x} for x in db.servers.find()]

        return entries, 200

    @api.expect(server)
    @api.marshal_with(server)
    def post(self):
        args = parser.parse_args()

        now = datetime.now().isoformat()

        entry = {
            'url': args['url'],
            'module': args['module'],
            'token': args['token'],
            'date_added': now,
            'date_updated': now,

        }

        db.servers.insert_one(entry)

        return entry, 201


@api.route('/server/<string:server_id>')
class Server(Resource):
    def delete(self, server_id):
        db.servers.delete_one({'_id': bson.ObjectId(server_id)})

        db.metrics.delete_many({'server_id': bson.ObjectId(server_id)})

        db.runs.delete_many({'server_id': bson.ObjectId(server_id)})

        return '', 204

    @api.expect(server)
    @api.marshal_with(server)
    def put(self, server_id):
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

        entry = db.servers.find_one_and_update(filter, update)

        return entry


@api.route('/server/<string:server_id>/metrics')
class MetricList(Resource):
    @api.marshal_with(listed_metric)
    def get(self, server_id):
        entries = [{'id': str(x['_id']), 'metric': x} for x in db.metrics.find({'server_id': bson.ObjectId(server_id)})]

        return entries, 200


def main():
    app.run(host='0.0.0.0', use_reloader=True, extra_files=['certification_service/*'])


if __name__ == '__main__':
    main()
