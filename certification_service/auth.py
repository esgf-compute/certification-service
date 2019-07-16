import click
from flask import g
from flask import redirect
from flask import request
from flask import session
from flask.cli import with_appcontext
from flask_openid import OpenID
from flask_restplus import Namespace, Resource

from certification_service.model import get_db

api = Namespace('auth', description='Authentication')


def init_app(app):
    oid = OpenID(app, safe_roots=['http://10.5.5.5:3000/admin'])

    @app.cli.command('whitelist-user')
    @click.argument('openid')
    @with_appcontext
    def whitelist_user(openid):
        db = get_db()

        db.users.insert_one({'openid': openid})

    @app.before_request
    def lookup_current_user():
        g.user = None

        if 'openid' in session:
            openid = session['openid']

            db = get_db()

            g.user = db.users.find_one({'openid': openid})

    @api.route('/login')
    class Login(Resource):
        def get(self):
            openid = session['openid'] = request.args['openid.identity']

            db = get_db()

            user = db.users.find_one({'openid': openid})

            if user is not None:
                g.user = user
            else:
                return {'message': 'User has not been whitelisted'}, 200

            return redirect(oid.get_next_url()+'?openid_complete=true')

        def post(self):
            if g.user is not None:
                return redirect(oid.get_next_url())

            x = oid.try_login('https://esgf-node.llnl.gov/esgf-idp/openid/')

            return {'redirect': x.location}, 200

    @api.route('/logout')
    class Logout(Resource):
        def get(self):
            if 'openid' in session:
                session.pop('openid')

            return redirect(oid.get_next_url())
