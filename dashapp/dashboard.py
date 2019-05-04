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
import plotly.graph_objs as go
from sqlalchemy import or_
import dash_daq as daq
import dash_html_components as html 

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
        html.Div(id='dummy_div'),
        # table
        html.Div([
            # meta
            html.Div([

                dcc.ConfirmDialog(
                    id='confirm',
                    message='Add rule?',
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
                html.P('Include:'),
                dcc.Dropdown(
                    id='include-category-dropdown',
                    options=[],
                    multi=True
                ),
                html.P('source:'),
                dcc.Dropdown(
                    id='source-dropdown',
                    options=[],
                    multi=True
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
                    editable=False,
                    sorting='be',
                    sorting_type='single',
                    sorting_settings=[{'column_id': 'date',
                                       'direction': 'asc'}],
                    column_static_dropdown=[]
                    # filtering=False,
                    # n_fixed_rows=1,
                )],
                     # style={'width': '49%', 'display': 'inline-block'}
            ),
            daq.ToggleSwitch(
                id='toggle-edit-table',
                label='Edit table',
                labelPosition='bottom',
                size=50,
                color='green'
            )
        ]),
        html.Div([

            html.Div([
                dcc.Graph(
                    id='category-pie',
                    figure={
                    }
                )
            ], className='six columns'),
            html.Div([
                dcc.Graph(
                    id='subcategory-pie',
                    figure={
                        'data': [

                        ],
                        'layout': {
                            'title': 'Subcategory'
                        }
                    }
                )
            ], className='six columns'),
        ], className="row"),

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
                    'maxHeight': '700',
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


@dashapp.callback(Output('subcategory-pie', 'figure'),
                  [Input('category-pie', 'clickData')],
                  [State('date-picker-range', 'start_date'),
                   State('date-picker-range', 'end_date')])
def display_click_data(clickData, start_date, end_date):
    if clickData is None:
        return []
    category_label = clickData['points'][0]['label']
    subcategories = current_user.categories.\
        filter(Category.name == category_label).first().subcategories.all()

    sd = (dt.strptime(start_date, '%Y-%m-%d'))
    ed = (dt.strptime(end_date, '%Y-%m-%d'))

    labels = []
    values = []
    for subcategory in subcategories:
        labels.append(subcategory.name)
        transactions = subcategory.transactions.filter(Transaction.date >= sd)\
                                               .filter(Transaction.date <= ed)\
                                               .filter(Transaction.amount >= 0)\
                                               .order_by(Transaction.column('date').asc())
        sum = 0
        for transaction in transactions:
            sum = sum + transaction.amount
        values.append(sum)

    pie = {
        'data': [
            go.Pie(labels=labels, values=values)
        ],
        'layout': {
            'title': category_label
        }
    }

    return pie


@dashapp.callback(Output('datatable-container', 'data'),
                  [Input('datatable-container', 'pagination_settings'),
                   Input('signal', 'children'),
                   Input('datatable-container', 'sorting_settings')],
                  [State('date-picker-range', 'start_date'),
                   State('date-picker-range', 'end_date'),
                   State('include-category-dropdown', 'value'),
                   State('source-dropdown', 'value')])
def update_table_pagination(pagination_settings,
                            children,
                            sorting_settings,
                            start_date,
                            end_date,
                            include_list,
                            source_list):
    if children is None:
        return None
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

    query = current_user.transactions.join(Subcategory).join(Category).\
        filter(Transaction.date >= sd).\
        filter(Transaction.date <= ed)

    if include_list is not None:
        conditions = [Category.name == category
                      for category in include_list]
        query = query.filter(or_(*conditions))

    if source_list is not None:
        conditions = [Transaction.source.contains(source)
                      for source in source_list]
        query = query.filter(or_(*conditions))

    # pagination of SQLAlchemy starts from 1
    query = query.order_by(order_by).\
        paginate(pagination_settings['current_page'] + 1,
                 pagination_settings['page_size'], False).items

    return ([tx.to_dict() for tx in query])


def subcategory_dropdown_list():
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
        tx['subcategory'] = untagged
        for rule in rules:
            if rule_matches(tx, rule):
                tx['subcategory'] = rule.subcategory


def categories_pie(start_date, end_date, include_list, source_list):
    sd = (dt.strptime(start_date, '%Y-%m-%d'))
    ed = (dt.strptime(end_date, '%Y-%m-%d'))

    query = current_user.transactions\
                        .join(Subcategory)\
                        .join(Category)\
                        .filter(Transaction.date >= sd)\
                        .filter(Transaction.date <= ed)\
                        .filter(Transaction.amount >= 0)

    if include_list is not None:
        conditions = [Category.name == category
                      for category in include_list]
        query = query.filter(or_(*conditions))

    if source_list is not None:
        conditions = [Transaction.source.contains(source)
                      for source in source_list]
        query = query.filter(or_(*conditions))

    transactions = query.order_by(Transaction .column('date').asc())

    total_sum = 0
    sums = {}
    for tx in transactions:
        if tx.subcategory.category.name in sums:
            sums[tx.subcategory.category.name] = \
                sums[tx.subcategory.category.name] + tx.amount
        else:
            sums[tx.subcategory.category.name] = tx.amount
    total_sum = int(sum(sums.values()))
    labels = [k for (k, v) in sums.items()]
    values = [v for (k, v) in sums.items()]

    pie = {
        'data': [
            go.Pie(labels=labels, values=values)
        ],
        'layout': {
            'title': start_date.replace('-', '.') + ' - '
            + end_date.replace('-', '.') + '<br>' + str(total_sum)+'₪'
        }
    }
    return pie


def remove_duplicates(new_transactions):
    min_date = min(new_transactions, key=lambda tx: tx['date'])['date']
    max_date = max(new_transactions, key=lambda tx: tx['date'])['date']
    transactions = current_user.transactions\
                               .filter(Transaction.date >= min_date)\
                               .filter(Transaction.date <= max_date)\
                               .order_by(Transaction.column('date').asc())

    filtered_transactions = []

    # TODO search with bisect
    for new_tx in new_transactions:
        found = False
        for old_tx in transactions:
            if new_tx['amount'] == old_tx.amount and \
               new_tx['date'] == old_tx.date and \
               new_tx['merchant'] == old_tx.merchant and \
               new_tx['comment'] == old_tx.comment and \
               new_tx['source'] == old_tx.source:
                found = True
                break
        if found is False:
            filtered_transactions.append(new_tx)

    return filtered_transactions


@dashapp.callback([Output('include-category-dropdown', 'options'),
                   Output('include-category-dropdown', 'value'),
                   Output('source-dropdown', 'options'),
                   Output('source-dropdown', 'value'),
                   Output('date-picker-range', 'start_date'),
                   Output('date-picker-range', 'end_date')],
                  [Input('dummy_div', 'children')])
def update_filtering_fields(dummy):
    include_category_values = [category.name
                               for category in current_user.categories.all()]
    include_category_options = [{'label': category, 'value': category}
                                for category in include_category_values]
    
    sources = [source.source for source in db.session.query(Transaction.source)
               .filter(Transaction.owner == current_user)
               .distinct().all()]
    source_options = [{'label': source, 'value': source}
                      for source in sources]
    return include_category_options, include_category_values, source_options,\
        sources, dt(2019, 1, 1),\
        dt(dt.now().year, dt.now().month, dt.now().day)


@dashapp.callback([Output('signal', 'children'),
                   Output('category-pie', 'figure'),
                   Output('monthly-graph', 'figure'),
                   Output('datatable-container', 'column_static_dropdown')],
                  [Input('datatable-upload', 'contents'),
                   Input('date-picker-range', 'start_date'),
                   Input('date-picker-range', 'end_date'),
                   Input('include-category-dropdown', 'value'),
                   Input('source-dropdown', 'value')],
                  [State('datatable-upload', 'filename')])
def update_output(contents, start_date, end_date, include_list, source_list, filename):

    if contents is not None:
        transactions = get_transactions(contents, filename)
        assign_subcategories(transactions)
        transactions = remove_duplicates(transactions)
        [db.session.add(Transaction.valueOf(tx, current_user))
         for tx in transactions]
        db.session.commit()

    return json.dumps({'start_date': start_date, 'end_date': end_date}),\
        categories_pie(start_date, end_date, include_list, source_list),\
        update_monthly_graph(),\
        subcategory_dropdown_list()


@dashapp.callback(
    [Output('confirm', 'displayed'), Output('confirm', 'message')],
    [Input('datatable-container', 'data_timestamp'),
     Input('datatable-container', 'data_previous')],
    [State('datatable-container', 'data')])
def update_columns(timestamp, prev_rows, rows):
    if (timestamp is None):
        return False, 'NONE'
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
                    return False, 'NONE'
    return False, 'NONE'


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


def update_monthly_graph():
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


@dashapp.callback(Output('datatable-container', 'editable'),
                  [Input('toggle-edit-table', 'value')])
def toggle_edit_table(value):
    return value

