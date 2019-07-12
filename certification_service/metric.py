import bson
from flask_restplus import Namespace, Resource, fields

from certification_service.model import db

api = Namespace('metric', description='Server metrics')

metric = api.model('Metric', {
    'state': fields.String,
    'data': fields.String,
    'date_added': fields.DateTime,
})

listed_metric = api.model('ListedMetric', {
    'id': fields.String(required=True),
    'metric': fields.Nested(metric),
})


@api.route('/<string:server_id>')
class MetricList(Resource):
    @api.marshal_with(listed_metric)
    def get(self, server_id):
        entries = [{'id': str(x['_id']), 'metric': x} for x in db.metrics.find({'server_id': bson.ObjectId(server_id)})]

        return entries, 200
