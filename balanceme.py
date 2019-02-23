from app import create_app, db
from app.models import User, Transaction


# Create Flask server app
server = create_app()

from dashapp import get_dashapp
balanceme = get_dashapp()


@server.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Transaction': Transaction}
