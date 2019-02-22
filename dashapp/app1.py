import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input
from dashapp import dashapp
import dash_table
from dashapp.parser.parse import get_transactions
from flask_login import current_user


colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

dashapp.layout = html.Div(style={},
                          children=[
                              html.H1(
                                  children='Balanceme',
                                  style={
                                      'textAlign': 'center',
                                      'color': colors['text']
                                  }
                              ),
                              dcc.Upload(
                                  id='datatable-upload',
                                  children=html.Div([
                                      'Drag and Drop or ',
                                      html.A('Select Files')
                                  ]),
                                  style={
                                      'width': '100%',
                                      'height': '60px',
                                      'lineHeight': '60px',
                                      'borderWidth': '1px',
                                      'borderStyle': 'dashed',
                                      'borderRadius': '5px',
                                      'textAlign': 'center',
                                      'margin': '10px'
                                  },
                              ),
                              dash_table.DataTable(
                                  
                                  style_table={
                                      'maxHeight': '300',
                                      'overflowY': 'scroll',
                                      'overflowX': 'scroll'
                                  },
                                  style_cell={
                                      'minWidth': '0px', 'maxWidth': '180px',
                                      'whiteSpace': 'no-wrap',
                                      'overflow': 'hidden',
                                      'textOverflow': 'ellipsis',
                                  },
                                  css=[{
                                      'selector': '.dash-cell div.dash-cell-value',
                                      'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                                  }],
                                  id='datatable-upload-container',
                                  columns=[{"name": label, "id": label} for label in ['date', 'merchant', 'amount', 'comment', 'source']],
                                  data=[],
                                  editable=True,
                                  filtering=True,
                                  sorting=True,
                                  sorting_type="multi",
                              ),

                              dcc.Graph(
                                  id='monthly-inout',
                                  figure={}
                              ),
                          ])


@dashapp.callback(Output('datatable-upload-container', 'data'),
                  [Input('datatable-upload', 'contents')],
                  [State('datatable-upload', 'filename')])
def update_output(contents, filename):
    if contents is None:
        return [{}]
    transactions = get_transactions(contents, filename)
    return transactions


@dashapp.callback(Output('monthly-inout', 'figure'),
                  [Input('datatable-upload', 'contents')])
def update_inout(contents):
    if contents is None:
        return {}

    figure = {
        'data': [
            {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Income'},
            {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Outcome'},
        ],
        'layout': {
            'title': 'Monthly Income/Outcome'
        }
    }
    return figure
