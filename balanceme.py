from app import create_app, db
from app.models import User, Transaction, Category, Subcategory, Rule

# Create Flask server app
server = create_app()


@server.shell_context_processor
def make_shell_context():
    return {'db': db,
            'User': User,
            'Transaction': Transaction,
            'Category': Category,
            'Subcategory': Subcategory,
            'Rule': Rule}
