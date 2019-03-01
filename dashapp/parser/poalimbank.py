import base64
import dateutil.parser
import pandas as pd
import io
from datetime import datetime
import math


def parse_row(row, source):
    date = None
    values_iterator = iter(row.values())
    try:
        date = (next(values_iterator).date())
        merchant = next(values_iterator)
        info = next(values_iterator)
        id = next(values_iterator)
        expense = next(values_iterator)
        income = next(values_iterator)
        next(values_iterator)
        next(values_iterator)
        to1 = next(values_iterator)
        to2 = next(values_iterator)

        amount = expense
        if math.isnan(amount):
            amount = (-1)*income

        comment = ''
        if pd.isnull(info) is False:
            comment = comment + ' ' + str(info)
        if pd.isnull(to1) is False:
            comment = comment + ' ' + str(to1)
        if pd.isnull(to2) is False:
            comment = comment + ' ' + str(to2)

        transaction = {'date': date, 'merchant': merchant, 'amount': amount,
                       'comment': comment, 'source': source}

        return transaction
    except Exception as e:
        return None


def get_source(row):
    for col in row.values():
        if 'מספר חשבון' in str(col):
            return 'Poalim Bank'
    return None


def get_transactions(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        table = pd.read_excel(io.BytesIO(decoded)).to_dict('records')
    except Exception as e:  # TODO catch decode error and not all
        return None

    source = 'Poalim Bank'
    transactions = []
    for row in table:
        new_source = get_source(row)
        if new_source is not None:
            source = new_source
        else:
            tx = parse_row(row, source)
            if tx is not None:
                transactions.append(tx)
    return transactions
