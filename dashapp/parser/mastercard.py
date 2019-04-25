import base64
import dateutil.parser
import pandas as pd
import io
from datetime import datetime


def parse_row(row, source):
    date = None
    values_iterator = iter(row.values())
    try:
        date = datetime.strptime(next(values_iterator), '%d/%m/%Y')
        merchant = next(values_iterator)
        # skip 
        next(values_iterator)
        next(values_iterator)
        amount = next(values_iterator)
        # skip 
        next(values_iterator)
        next(values_iterator)
        comment = next(values_iterator)
        if pd.isna(comment):
            comment = ''
        transaction = {'date': date, 'merchant': merchant, 'amount': amount,
                       'comment': comment, 'source': source}

        return transaction
    except Exception as e:
        return None


def get_source(row):
    for col in row.values():
        if 'מסטרקארד' in str(col):
            return col
    return None


def get_transactions(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        table = pd.read_excel(io.BytesIO(decoded)).to_dict('records')
    except Exception as e:  # TODO catch decode error and not all
        return None
    source = 'Mastercard'
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
