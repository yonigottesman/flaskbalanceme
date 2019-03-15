import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input
from dashapp import dashapp
import dash_table
from dashapp.parser.parse import get_transactions
from flask_login import current_user
from app import db
from app.models import Transaction, Category, Subcategory, Rule
from datetime import datetime as dt
import json
from itertools import groupby
from datetime import timedelta

import pandas as pd
from collections import OrderedDict

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
                 {'name': 'subcategory', 'id': 'subcategory',
                  'presentation': 'dropdown'}]

dashapp.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


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
                                       'direction': 'asc'}],
                    column_static_dropdown=[]
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
                    html.Button('Add Category', id='add-category-button',
                                n_clicks=0)
                ], style={'height': 50}),
            ], className="six columns"),
            html.Div([
                html.Div(id='edit-null-div2', style={'display': 'none'}),
                dash_table.DataTable(
                    style_table={
                        'maxHeight': '300',
                        'overflowY': 'scroll',
                        # 'overflowX': 'scroll'
                    },
                    id='subcategory-container',
                    columns=[{'name': 'Subcategory', 'id': 'subcategory'},
                             {'name': 'Category', 'id': 'category'}],
                    data=[],
                    editable=True,
                    sorting=False,
                    # row_deletable=True
                ),

                html.Div([
                    html.Div([
                        dcc.Input(
                            id='add-subcategory-name',
                            placeholder='New Subcategory',
                            value='',
                            style={'padding': 10}
                        ),
                    ], className='four columns'),
                    html.Div([
                        dcc.Dropdown(
                            id='add-subcategory-category',
                            options=[],
                            value=None
                        ),
                    ], className='four columns'),
                    html.Div([
                        html.Button('Add Subcategory',
                                    id='add-subcategory-button',
                                    n_clicks=0)
                    ], className='four columns'),
                ], className="row"),
            ], className="six columns")
        ], className="row"),

        html.Div([
            dash_table.DataTable(
                style_table={
                    'maxHeight': '300',
                    'overflowY': 'scroll',
                    # 'overflowX': 'scroll'
                },
                id='rules-container',
                columns=[{'name': 'Contains', 'id': 'contains'},
                         {'name': 'Subcategory', 'id': 'subcategory'}],
                data=[],
                editable=True,
                sorting=False,
                # row_deletable=True
            ),

            html.Div([
                html.Div([
                    dcc.Input(
                        id='add-rule-text',
                        placeholder='Transaction text contains',
                        value='',
                        style={'padding': 10}
                    ),
                ], className='four columns'),
                html.Div([
                    dcc.Dropdown(
                        id='add-rule-subcategory',
                        options=[],
                        value=None
                    ),
                ], className='four columns'),
                html.Div([
                    html.Button('Add Rule',
                                id='add-rule-button',
                                n_clicks=0)
                ], className='four columns'),
            ], className="row"),
        ])
    ])


@dashapp.callback(Output('datatable-container', 'data'),
                  [Input('datatable-container', 'pagination_settings'),
                   Input('signal', 'children'),
                   Input('datatable-container', 'sorting_settings')])
def update_table(pagination_settings, children, sorting_settings):
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


@dashapp.callback(Output('datatable-container', 'column_static_dropdown'),
                  [Input('signal', 'children')])
def update_graph2(signal):

    subcategories = [sub.name for sub in current_user.subcategories.all()]
    column_static_dropdown = [
        {
            'id': 'subcategory',
            'dropdown': [
                {'label': i, 'value': i}
                for i in subcategories
            ]
        }
    ]
    return column_static_dropdown


def rule_matches(transaction, rule):
    if rule.text in transaction['merchant'] or \
       rule.text in transaction['comment']:
        return True
    else:
        return False


def assign_subcategories(transactions):
    rules = current_user.rules.all()
    untagged = current_user.subcategories\
                           .filter(Subcategory.name == 'untagged').first()
    for tx in transactions:
        for rule in rules:
            if rule_matches(tx, rule):
                tx['subcategory'] = rule.subcategory
            else:
                tx['subcategory'] = untagged


@dashapp.callback(Output('signal', 'children'),
                  [Input('datatable-upload', 'contents'),
                   Input('date-picker-range', 'start_date'),
                   Input('date-picker-range', 'end_date')],
                  [State('datatable-upload', 'filename')])
def update_output(contents, start_date, end_date, filename):

    if contents is not None:

        transactions = get_transactions(contents, filename)
        assign_subcategories(transactions)
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
                sc = current_user.subcategories.filter(Subcategory.name
                                                       == curr['subcategory'])\
                                               .first()
                curr['subcategory'] = sc
                if sc is not None:
                    tx.update(curr)
                    db.session.commit()


@dashapp.callback(Output('category-container', 'data'),
                  [Input('add-category-button', 'n_clicks')],
                  [State('category-container', 'data'),
                   State('add-category-name', 'value')])
def update_categories(clicks, categories, new_category):
    if new_category is not '':
        current = current_user.categories.\
            filter(Category.name == new_category).first()
        if current is None:
            category = Category(name=new_category, owner=current_user)
            db.session.add(category)
            db.session.commit()
    return [{'name': tx.name} for tx in current_user.categories.all()]


@dashapp.callback(Output('subcategory-container', 'data'),
                  [Input('add-subcategory-button', 'n_clicks')],
                  [State('subcategory-container', 'data'),
                   State('add-subcategory-name', 'value'),
                   State('add-subcategory-category', 'value')])
def add_subcategories(clicks, subcategories,
                      new_subcategory_name,
                      new_subcategory_category):
    if new_subcategory_name is not '' and new_subcategory_category is not None:
        current = current_user.subcategories.\
            filter(Subcategory.name == new_subcategory_name).first()
        if current is None:
            category = current_user.categories.\
                filter(Category.name == new_subcategory_category).first()
            if category is not None:
                subcategory = Subcategory(name=new_subcategory_name,
                                          owner=current_user,
                                          category=category)
                db.session.add(subcategory)
                db.session.commit()
    return [{'subcategory': tx.name, 'category': tx.category.name}
            for tx in current_user.subcategories.all()]


@dashapp.callback(
    Output('edit-null-div2', 'children'),
    [Input('subcategory-container', 'data_timestamp'),
     Input('subcategory-container', 'data_previous')],
    [State('subcategory-container', 'data')])
def update_subcategories(timestamp, prev_rows, rows):
    if timestamp is None:
        return

    for prev, curr in zip(prev_rows, rows):
        if (prev != curr):
            pass
            # tx_id = prev['tx_id']
            # txs = current_user.transactions.filter(Transaction.id == tx_id)\
            #                                .all()
            # if len(txs) == 1:
            #     tx = txs[0]
            #     tx.update(curr)
            #     db.session.commit()


def play_rule(rule):
    transactions = current_user.transactions.all()
    for transaction in transactions:
        if rule.text in transaction.merchant or \
           rule.text in transaction.comment:
            transaction.subcategory = rule.subcategory
    

@dashapp.callback(Output('rules-container', 'data'),
                  [Input('add-rule-button', 'n_clicks')],
                  [State('rules-container', 'data'),
                   State('add-rule-text', 'value'),
                   State('add-rule-subcategory', 'value')])
def update_rules(clicks, rules,
                 new_rule_text,
                 new_rule_subcategory):
    if new_rule_text is not '' and new_rule_subcategory is not None:
        current = current_user.rules.\
            filter(Rule.text == new_rule_text).first()
        if current is None:
            subcategory = current_user.subcategories.\
                filter(Subcategory.name == new_rule_subcategory).first()
            if subcategory is not None:
                rule = Rule(text=new_rule_text,
                            owner=current_user,
                            subcategory=subcategory)
                db.session.add(rule)
                play_rule(rule)
                db.session.commit()
    return [{'contains': tx.text, 'subcategory': tx.subcategory.name}
            for tx in current_user.rules.all()]


@dashapp.callback(Output('add-subcategory-category', 'options'),
                  [Input('category-container', 'data')])
def update_subcategory_add_dropdown(data):
    return [{'label': i['name'], 'value': i['name']} for i in data]


@dashapp.callback(Output('add-rule-subcategory', 'options'),
                  [Input('subcategory-container', 'data')])
def update_rule_add_dropdown(data):
    return [{'label': i['subcategory'], 'value': i['subcategory']}
            for i in data]


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
            'title': 'Monthly Aggregations',
            'xaxis': {'tickformat': '%Y-%m',
                      # 'dtick': 86400000.0*30,
                      'range': [dt.now() - timedelta(days=365), dt.now()]}
        }
    }
    return figure
