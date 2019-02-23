import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input
from dashapp import dashapp
import dash_table
from dashapp.parser.parse import get_transactions
from flask_login import current_user
from app import db
from app.models import Transaction
from datetime import datetime as dt
import json


colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
TX_PAGE_SIZE = 5

table_columns = [{'name': 'date', 'id': 'date', 'editable': False},
                 {'name': 'merchant', 'id': 'merchant'},
                 {'name': 'amount', 'id': 'amount'},
                 {'name': 'comment', 'id': 'comment'},
                 {'name': 'source', 'id': 'source'},
                 {'name': 'tx-id', 'id': 'tx_id', 'hidden': True}]


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
                              
                              dcc.DatePickerRange(
                                  id='date-picker-range',
                                  start_date=dt(2019, 1, 1),
                                  end_date=dt(2019, 2, 1),
                              ),
                              
                              dash_table.DataTable(
                                  pagination_mode='be',
                                  pagination_settings={
                                      'current_page': 0,
                                      'page_size': TX_PAGE_SIZE
                                  },
                                  style_table={
                                      'maxHeight': '300',
                                      'overflowY': 'scroll',
                                      # 'overflowX': 'scroll'
                                  },
                                  # style_cell={
                                  #     'minWidth': '0px', 'maxWidth': '180px',
                                  #     'whiteSpace': 'no-wrap',
                                  #     'overflow': 'hidden',
                                  #     'textOverflow': 'ellipsis',
                                  # },
                                  # css=[{
                                  #     'selector': '.dash-cell div.dash-cell-value',
                                  #     'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                                  # }],
                                  id='datatable-container',
                                  columns=table_columns,
                                  data=[],
                                  editable=True,
                                  sorting='be',
                                  sorting_type='single',
                                  sorting_settings=[{'column_id': 'date', 'direction': 'asc'}]
                                  # filtering=False,
                                  # n_fixed_rows=1,
                              ),
                              
                              html.Button('Add Transaction', id='editing-rows-button', n_clicks=0),
                              
                              dcc.Graph(
                                  id='monthly-inout',
                                  figure={}
                              ),
                              
                              # Hidden div inside the app that stores the intermediate value
                              html.Div(id='signal', style={'display': 'none'}),
                              html.Div(id='edit-null-div', style={'display': 'none'})
                          ])


@dashapp.callback(Output('datatable-container', 'data'),
                  [Input('datatable-container', 'pagination_settings'),
                   Input('signal', 'children'),
                   Input('datatable-container', 'sorting_settings')])
def update_graph(pagination_settings, children, sorting_settings):
    if len(sorting_settings) == 0:
        order_by = Transaction.column('date').asc()
    else:
        field = Transaction.column(sorting_settings[0]['column_id'])
        if (sorting_settings[0]['direction'] == 'asc'):
            order_by = field.asc()
        else:
            order_by = field.desc()

    hidden_dict = json.loads(children)
    sd = (dt.strptime(hidden_dict['start_date'], '%Y-%m-%d'))
    ed = (dt.strptime(hidden_dict['end_date'], '%Y-%m-%d'))

    return ([tx.to_dict() for tx in current_user.transactions.
             filter(Transaction.date >= sd).
             filter(Transaction.date <= ed).
             order_by(order_by).
             # pagination of SQLAlchemy starts from 1
             paginate(pagination_settings['current_page'] + 1,
                      pagination_settings['page_size'], False).items])


@dashapp.callback(Output('signal', 'children'),
                  [Input('datatable-upload', 'contents'),
                   Input('date-picker-range', 'start_date'),
                   Input('date-picker-range', 'end_date')],
                  [State('datatable-upload', 'filename')])
def update_output(contents, start_date, end_date, filename):

    if contents is not None:
        transactions = get_transactions(contents, filename)
        [db.session.add(Transaction.valueOf(tx, current_user))
         for tx in transactions]
        db.session.commit()

    return json.dumps({'start_date': start_date, 'end_date': end_date})


@dashapp.callback(
    Output('edit-null-div', 'children'),
    [Input('datatable-container', 'data_timestamp'),
     Input('datatable-container', 'data_previous')],
    [State('datatable-container', 'data')])
def update_columns(timestamp, prev_rows, rows):
    if (timestamp is None):
        return None

    # Find changed transaction
    for prev, curr in zip(prev_rows, rows):
        if (prev != curr):
            tx_id = prev['tx_id']
            txs = current_user.transactions.filter(Transaction.id == tx_id)\
                                           .all()
            if len(txs) == 1:
                tx = txs[0]
                tx.update(curr)
                db.session.commit()


@dashapp.callback(Output('monthly-inout', 'figure'),
                  [Input('datatable-container', 'data')])
def update_inout(data):

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
