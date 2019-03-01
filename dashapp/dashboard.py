import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input
from dashapp import dashapp
import dash_table
from dashapp.parser.parse import get_transactions
from flask_login import current_user
from app import db
from app.models import Transaction, Category, Subcategory
from datetime import datetime as dt
import json
from itertools import groupby
from datetime import timedelta

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
TX_PAGE_SIZE = 20

table_columns = [{'name': 'date', 'id': 'date', 'editable': False},
                 {'name': 'merchant', 'id': 'merchant'},
                 {'name': 'amount', 'id': 'amount'},
                 {'name': 'comment', 'id': 'comment'},
                 {'name': 'source', 'id': 'source'},
                 {'name': 'tx-id', 'id': 'tx_id', 'hidden': True},
                 {'name': 'subcategory', 'id': 'subcategory'}]


dashapp.layout = html.Div(
    [
        # table 
        html.Div([
            # meta
            html.Div([
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
                # Hidden div inside the app that stores the intermediate value
                html.Div(id='signal', style={'display': 'none'}),
                html.Div(id='edit-null-div', style={'display': 'none'})],
                     # style={'width': '49%', 'display': 'inline-block'}
            ),
            html.Div([
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
                    id='datatable-container',
                    columns=table_columns,
                    data=[],
                    editable=True,
                    sorting='be',
                    sorting_type='single',
                    sorting_settings=[{'column_id': 'date',
                                       'direction': 'asc'}]
                    # filtering=False,
                    # n_fixed_rows=1,
                )],
                     # style={'width': '49%', 'display': 'inline-block'}
            )
        ]),

        html.Div([

            dcc.Graph(
                id='monthly-graph',
                figure={}
            ),
        ]),
        
        html.Div([
            dash_table.DataTable(
                style_table={
                    'maxHeight': '300',
                    'overflowY': 'scroll',
                    # 'overflowX': 'scroll'
                },
                id='category-container',
                columns=[{'name': 'name', 'id': 'name'}],
                data=[],
                editable=True,
                sorting=False,
                # row_deletable=True
            ),

            html.Div([
                dcc.Input(
                    id='add-category-name',
                    placeholder='New Category',
                    value='',
                    style={'padding': 10}
                ),
                html.Button('Add Category', id='add-category-button', n_clicks=0)
            ], style={'height': 50}),
        ])
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
        untagged = current_user.subcategories\
                               .filter(Subcategory.name == 'untagged').first()
        transactions = get_transactions(contents, filename)
        [db.session.add(Transaction.valueOf(tx, current_user, untagged))
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


@dashapp.callback(Output('category-container', 'data'),
                  [Input('add-category-button', 'n_clicks')],
                  [State('category-container', 'data'),
                   State('add-category-name', 'value')])
def update_categories(clicks, categories, new_category):
    if new_category is not '':
        current = current_user.categories.filter(Category.name == new_category).first()
        if current is None:
            category = Category(name=new_category, owner=current_user)
            db.session.add(category)
            db.session.commit()
    return [{'name': tx.name} for tx in current_user.categories.all()]


@dashapp.callback(Output('monthly-graph', 'figure'),
                  [Input('signal', 'children')])
def update_monthly_graph(date):
    data_outcome = current_user.transactions.filter(Transaction.amount >= 0).\
        order_by(Transaction.column('date').asc())
    data_income = current_user.transactions.filter(Transaction.amount < 0).\
        order_by(Transaction.column('date').asc())

    outcome_aggregation = []
    income_aggregation = []
    
    for k, g in groupby(data_outcome, lambda x: (x.date.year, x.date.month)):
        month = str(k[0])+"-"+str(k[1])
        month_sum = 0
        for tx in g:
            month_sum = month_sum + tx.amount
        outcome_aggregation.append((month, month_sum))

    for k, g in groupby(data_income, lambda x: (x.date.year, x.date.month)):
        month = str(k[0])+"-"+str(k[1])
        month_sum = 0
        for tx in g:
            month_sum = month_sum + tx.amount
        income_aggregation.append((month, month_sum))

    figure = {
        'data': [
            {'x': [x[0] for x in outcome_aggregation],
             'y': [x[1] for x in outcome_aggregation],
             'type': 'bar',
             'name': 'Expense'},
            {'x': [x[0] for x in income_aggregation],
             'y': [x[1]*(-1) for x in income_aggregation],
             'type': 'bar',
             'name': 'Income'},
        ],
        'layout': {
            'title': 'Dash Data Visualization',
            # ,
            # 
            'xaxis': {'tickformat': '%Y-%m',
                      # 'dtick': 86400000.0*30,
                      'range': [dt.now() - timedelta(days=365), dt.now()]}
        }
    }
    return figure
