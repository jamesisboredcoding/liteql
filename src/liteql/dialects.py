class SQLITE:
    """The dialect for SQLite"""

class MYSQL:
    """The dialect for MySQL"""

def _dialect(scheme):
    schemes = {
        "sqlite": SQLITE,
        "mysql": MYSQL
    }
    return schemes[scheme]