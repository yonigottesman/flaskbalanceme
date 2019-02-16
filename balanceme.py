from app import create_app, db
from app.models import User

from datetime import datetime as dt

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input
from dash.dependencies import Output
from flask_login import login_required


# Method to protect dash views/routes
def protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


# Create Flask server app
server = create_app()
balanceme = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')

protect_dashviews(balanceme)


            
balanceme.layout = html.Div([
    html.H1('Stock Tickers'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[
            {'label': 'Coke', 'value': 'COKE'},
            {'label': 'Tesla', 'value': 'TSLA'},
            {'label': 'Apple', 'value': 'AAPL'}
        ],
        value='COKE'
    ),
    dcc.Graph(id='my-graph')
], style={'width': '500'})


@balanceme.callback(Output('my-graph', 'figure'), [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    
    return {
        'data': [{
            'x': ['a','b'],
            'y': [1,2]
        }],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


@server.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}
