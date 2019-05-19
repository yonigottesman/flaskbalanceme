from app.parser.visacal import get_transactions as get_visa
from app.parser.mastercard import get_transactions as get_mastercard
from app.parser.poalimbank import get_transactions as get_poalim


def get_transactions(contents, filename):
    funcs = [get_visa, get_mastercard, get_poalim]
    for fun in funcs:
        retval = fun(contents, filename)
        if retval is not None and len(retval) > 0:
            return retval
    return []

