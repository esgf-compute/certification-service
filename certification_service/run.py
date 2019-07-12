import bson
from flask_restplus import Namespace, Resource, fields

from certification_service.model import db

api = Namespace('run', description='Certification runs')

run = api.model('Run', {
    'state': fields.String,
    'data': fields.String,
    'date_added': fields.DateTime,
})

listed_run = api.model('ListedRun', {
    'id': fields.String(required=True),
    'run': fields.Nested(run),
})


@api.route('/<string:server_id>')
class RunList(Resource):
    @api.marshal_with(listed_run)
    def get(self, server_id):
        entries = [{'id': str(x['_id']), 'run': x} for x in db.runs.find({'server_id': bson.ObjectId(server_id)})]

        return entries, 200
