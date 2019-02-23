import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input
from dashapp import dashapp
import dash_table
from dashapp.parser.parse import get_transactions
from flask_login import current_user
from app import db
from app.models import User, Transaction
from datetime import datetime as dt

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
TX_PAGE_SIZE = 5
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
                                  columns=[{"name": label, "id": label} for label in ['date', 'merchant', 'amount', 'comment', 'source']],
                                  data=[],
                                  editable=True,
                                  # filtering=False,
                                  # sorting=True,
                                  # sorting_type="single",
                                  # n_fixed_rows=1,
                              ),
                              html.Button('Add Transaction', id='editing-rows-button', n_clicks=0),
                              dcc.Graph(
                                  id='monthly-inout',
                                  figure={}
                              ),
                          ])


@dashapp.callback(Output('datatable-container', 'data'),
                  [Input('datatable-upload', 'contents'),
                   Input('date-picker-range', 'start_date'),
                   Input('date-picker-range', 'end_date'),
                   Input('datatable-container', 'pagination_settings')],
                  [State('datatable-upload', 'filename')])
def update_output(contents, start_date, end_date, pagination_settings, filename):
    print(pagination_settings)
    if contents is not None:
        transactions = get_transactions(contents, filename)
        [db.session.add(Transaction.valueOf(tx, current_user)) for tx in transactions]
        db.session.commit()

    sd = (dt.strptime(start_date, '%Y-%m-%d'))
    ed = (dt.strptime(end_date, '%Y-%m-%d'))

    return ([tx.to_dict() for tx in current_user.transactions.
             filter(Transaction.date >= sd).
             filter(Transaction.date <= ed)])


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
