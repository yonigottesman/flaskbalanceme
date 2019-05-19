from datetime import datetime as dt
from dash.dependencies import Output, State, Input
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State, Input

import dash_table
from app.parser.parse import get_transactions
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

def register_callbacks(dashapp):
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


    def filter_query(start_date, end_date,
                     category_list, source_list, search_string):

        sd = (dt.strptime(start_date, '%Y-%m-%d'))
        ed = (dt.strptime(end_date, '%Y-%m-%d'))

        query = current_user.transactions.join(Subcategory).join(Category).\
            filter(Transaction.date >= sd).\
            filter(Transaction.date <= ed)

        if category_list is not None:
            conditions = [Category.name == category
                          for category in category_list]
            query = query.filter(or_(*conditions))

        if source_list is not None:
            conditions = [Transaction.source.contains(source)
                          for source in source_list]
            query = query.filter(or_(*conditions))

        if search_string is not None:
            conditions = [Transaction.merchant.contains(search_string),
                          # Transaction.amount.contains(search_string),
                          Transaction.comment.contains(search_string)]
            query = query.filter(or_(*conditions))

        return query


    @dashapp.callback(Output('datatable-container', 'data'),
                      [Input('datatable-container', 'pagination_settings'),
                       Input('signal', 'children'),
                       Input('datatable-container', 'sorting_settings')],
                      [State('date-picker-range', 'start_date'),
                       State('date-picker-range', 'end_date'),
                       State('include-category-dropdown', 'value'),
                       State('source-dropdown', 'value'),
                       State('search-input', 'value')])
    def update_table_pagination(pagination_settings,
                                signal,
                                sorting_settings,
                                start_date,
                                end_date,
                                include_list,
                                source_list,
                                search_string):
        if signal is None:
            return None
        if len(sorting_settings) == 0:
            order_by = Transaction.column('date').asc()
        else:
            field = Transaction.column(sorting_settings[0]['column_id'])
            if (sorting_settings[0]['direction'] == 'asc'):
                order_by = field.asc()
            else:
                order_by = field.desc()

        query = filter_query(start_date,
                             end_date, include_list, source_list, search_string)

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


    def categories_pie(start_date,
                       end_date,
                       include_list,
                       source_list,
                       search_string):

        transactions = filter_query(start_date, end_date, include_list,
                                    source_list, search_string)\
                                    .filter(Transaction.amount >= 0)\
                                    .order_by(Transaction .column('date').asc())

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
        min_date = min(new_transactions, key=lambda tx: tx['date'])['date'] - timedelta(days=1)
        max_date = max(new_transactions, key=lambda tx: tx['date'])['date'] + timedelta(days=1)
        transactions = current_user.transactions\
                                   .filter(Transaction.date >= min_date)\
                                   .filter(Transaction.date <= max_date)\
                                   .order_by(Transaction.column('date').asc())

        filtered_transactions = []

        # TODO search with bisect
        for new_tx in new_transactions:
            found = False
            for old_tx in transactions:
                if (new_tx['amount'] == old_tx.amount or new_tx['amount'] == -1*old_tx.amount) and \
                   (new_tx['date'] == old_tx.date or new_tx['date'] == old_tx.date.date()) and \
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
                       Input('source-dropdown', 'value'),
                       Input('search-input', 'value')],
                      [State('datatable-upload', 'filename')])
    def update_output(contents, start_date, end_date, include_list,
                      source_list, search_string, filename):

        if contents is not None:
            transactions = get_transactions(contents, filename)
            assign_subcategories(transactions)
            transactions = remove_duplicates(transactions)
            [db.session.add(Transaction.valueOf(tx, current_user))
             for tx in transactions]
            db.session.commit()

        return json.dumps({'start_date': start_date, 'end_date': end_date}),\
            categories_pie(start_date, end_date, include_list, source_list, search_string),\
            update_monthly_graph(),\
            subcategory_dropdown_list()


    @dashapp.callback(
        [Output('confirm', 'displayed'), Output('confirm', 'message')],
        [Input('datatable-container', 'data_timestamp'),
         Input('datatable-container', 'data_previous')],
        [State('datatable-container', 'data')])
    def update_table(timestamp, prev_rows, rows):

        if (timestamp is None):
            return False, 'NONE'

        for prev_row in prev_rows:
            curr_row = list(filter(lambda tx: tx['tx_id'] == prev_row['tx_id'], rows))
            if len(curr_row) == 0 or curr_row[0] != prev_row:
                tx_id = prev_row['tx_id']
                tx = current_user.transactions.filter(Transaction.id == tx_id)\
                                              .first()
                if len(curr_row) == 0:
                    db.session.delete(tx)
                    db.session.commit()
                else:
                    curr_row = curr_row[0]
                    sc = current_user\
                        .subcategories\
                        .filter(Subcategory.name == curr_row['subcategory'])\
                        .first()
                    curr_row['subcategory'] = sc
                    if sc is not None:
                        tx.update(curr_row)
                        db.session.commit()
                break
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


    @dashapp.callback([Output('datatable-container', 'editable'),
                       Output('datatable-container', 'row_deletable')],
                      [Input('toggle-edit-table', 'value')])
    def toggle_edit_table(value):
        return value,value
