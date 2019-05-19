import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input
import dash_table
# from dashapp.parser.parse import get_transactions



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


layout = html.Div([
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
            html.Div([
                html.Div([
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=dt(2019, 1, 1),
                        end_date=dt(2019, 2, 1),
                    )
                ], className="four columns"),
                html.Div([
                    dcc.Input(id='search-input', type='text', placeholder='Search transaction')
                ], className="four columns"),
            ], className="row"),
            # html.P('Include:'),
            dcc.Dropdown(
                id='include-category-dropdown',
                options=[],
                multi=True
            ),
            # html.P('source:'),
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
                    'maxHeight': '3000',
                    'overflowY': 'scroll',
                    # 'overflowX': 'scroll'
                },
                id='datatable-container',
                columns=table_columns,
                n_fixed_rows=1,
                data=[],
                editable=False,
                row_deletable=False,
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


# layout = html.Div([
#     html.H1('Stock Tickers'),
#     dcc.Dropdown(
#         id='my-dropdown',
#         options=[
#             {'label': 'Coke', 'value': 'COKE'},
#             {'label': 'Tesla', 'value': 'TSLA'},
#             {'label': 'Apple', 'value': 'AAPL'}
#         ],
#          value='COKE'
#     ),
#     dcc.Graph(id='my-graph')
# ], style={'width': '500'})
