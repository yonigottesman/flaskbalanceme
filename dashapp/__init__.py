import dash
from flask_login import login_required
from app import create_app
from balanceme import server

# Method to protect dash views/routes
def protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


dashapp = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')
protect_dashviews(dashapp)

def get_dashapp():
    return dashapp

from dashapp import app1
