from flask import Flask
from flask_restplus import Api


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)

    api = Api(app)

    from certification_service import model # noqa

    from certification_service.metric import api as ns_metric
    from certification_service.run import api as ns_run
    from certification_service.server import api as ns_server

    api.add_namespace(ns_metric)
    api.add_namespace(ns_run)
    api.add_namespace(ns_server)

    return app
