import json

import bson
import pymongo
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource # noqa

app = Flask(__name__)

api = Api(app)

client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

db = client['certification']

servers = db['servers']

metrics = db['metrics']

servers.create_index('url', unique=True)

parser = reqparse.RequestParser()

parser.add_argument('url')


class ServerList(Resource):
    def get(self):
        entries = {}

        for x in servers.find():
            id = str(x['_id'])

            entries[id] = {
                'url': x['url']
            }

        return entries, 200

    def post(self):
        args = parser.parse_args()

        entry = {
            'url': args['url'],
        }

        servers.insert_one(entry)

        del entry['_id']

        return entry, 201


class MetricsList(Resource):
    def get(self, server_id):
        entries = {}

        server = servers.find_one({'_id': bson.ObjectId(server_id)})

        for x in metrics.find({'server_id': server['_id']}):
            entries[str(x['_id'])] = {'created': str(x['created'])}

        return entries, 200


class Metric(Resource):
    def get(self, server_id, metric_id):
        entry = metrics.find_one({'_id': bson.ObjectId(metric_id), 'server_id': bson.ObjectId(server_id)})

        del entry['_id']
        del entry['server_id']

        entry['created'] = str(entry['created'])
        entry['data'] = json.loads(entry['data'])

        return entry, 200


api.add_resource(ServerList, '/servers')
api.add_resource(MetricsList, '/server/<server_id>/metrics')
api.add_resource(Metric, '/server/<server_id>/metric/<metric_id>')


def main():
    app.run(host='0.0.0.0', use_reloader=True, extra_files=['certification_service/*'])


if __name__ == '__main__':
    main()
