from dashapp.parser.visacal import get_visa


def get_transactions(contents, filename):
    visa = get_visa(contents, filename)
    if visa is None:
        return []
    else:
        return visa
