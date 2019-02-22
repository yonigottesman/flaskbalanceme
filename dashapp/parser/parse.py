from dashapp.parser.visacal import get_visa


def get_transactions(contents, filename):
    return get_visa(contents, filename)
