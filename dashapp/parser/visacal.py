import pandas as pd
import base64
import io
import dateutil.parser


def is_visa(decoded_file):
    if 'פירוט עסקות נכון לתאריך' not in decoded_file:
        return False
    if 'לכרטיס ויזה' not in decoded_file:
        return False
    if 'המסתיים בספרות' not in decoded_file:
        return False
    return True


def get_date(string):
    try:
        date = dateutil.parser.parse(string, dayfirst=True)
    except Exception:
        return None
    else:
        return date


def parse_transaction(line, source):
    splits = line.split("\t")
    if len(splits) != 4 and len(splits) != 5:
        return None

    date = get_date(splits[0])
    if date is None:
        return None

    merchant = splits[1]
    amount = splits[3].replace("₪", '').replace(',', '').strip()

    if '-' in amount:
        amount = '-' + amount.replace('-', '')
    amount = float(amount)
    comment = ""
    if len(splits) == 5:
        comment = line.split("\t")[4]

    transaction = {'date': date, 'merchant': merchant, 'amount': amount,
                   'comment': comment, 'source': source}
    return transaction


def get_visa(contents, filename):

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    decoded_file = decoded.decode('utf-16')
    source_type = "visa"
    source_type_id = str(decoded_file.split("\n")[1].split("המסתיים בספרות")[1]
                         .split(",")[0])
    source = source_type+' '+source_type_id

    transactions = []
    for line in decoded_file.split('\n'):
        transaction = parse_transaction(line, source=source)
        if transaction is not None:
            transactions.append(transaction)
    return transactions
