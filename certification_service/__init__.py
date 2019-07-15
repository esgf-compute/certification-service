def create_app(test_config=None):
    import os

    from flask import Flask
    from flask_restplus import Api

    app = Flask(__name__)

    app.config['DATABASE'] = os.environ.get('DATABASE', 'mongodb://127.0.0.1:27017/')

    app.config['SECRET_KEY'] = 'secret'

    if test_config is not None:
        app.config.update(test_config)

    @app.route('/login', methods=('GET',))
    def login():
        return '''
        <form method="post" action="/auth/login">
            <input type="submit" value="Login">
        </form>
        <form method="get" action="/auth/logout">
            <input type="submit" value="Logout">
        </form>
        '''

    api = Api(app)

    from certification_service import auth

    auth.init_app(app)

    from certification_service import model # noqa

    model.init_app(app)

    from certification_service.auth import api as ns_auth
    from certification_service.metric import api as ns_metric
    from certification_service.run import api as ns_run
    from certification_service.server import api as ns_server

    api.add_namespace(ns_auth)
    api.add_namespace(ns_metric)
    api.add_namespace(ns_run)
    api.add_namespace(ns_server)

    return app
