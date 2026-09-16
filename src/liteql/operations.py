from .errors import LiteQLOperationError

def _match_condition(key, condition):
    if isinstance(condition, LiteQLOperation):
        setattr(condition, "_key", key)
    match condition:
        case str(): return f"{key} = '{condition}'"
        case int(): return f"{key} = {condition}"
        case LiteQLOperator(): return f"{key} {condition} {condition.value}"
        case _: return f"{key + " " if not condition._dont else ""}{condition}"

class LiteQLOperation:
    """Operation for LiteQL queries"""

class LiteQLOperator(LiteQLOperation):
    """Mathematical LiteQL operators"""
    sql: str
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.sql

class NOT(LiteQLOperation):
    def __init__(self, operation):
        self.op = operation

    def __str__(self):
        if type(self.op) == NOT:
            raise LiteQLOperationError("Cannot stack NOT operations")
        return f"NOT {self.op}"

class RAW(LiteQLOperation):
    def __init__(self, **kwargs):
        self.conditions = kwargs

    def __str__(self):
        cds = []
        for key in self.conditions.keys():
            condition = self.conditions[key]
            cds.append(_match_condition(key, condition))
        return " AND ".join(cds)

class GT(LiteQLOperator):
    """Greater than (>)"""
    sql = ">"

class GTE(LiteQLOperator):
    "Greater than or equal (>=)"
    sql = ">="

class LT(LiteQLOperator):
    "Less than (<)"
    sql = "<"

class LTE(LiteQLOperator):
    """Less than or equal (<=)"""
    sql = "<="

class NE(LiteQLOperator):
    """Not equal (!=)"""
    sql = "!="

class LIKE(LiteQLOperation):
    """Like (LIKE)"""
    sql = "LIKE"

class BETWEEN(LiteQLOperation):
    """Value1 between value2"""
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2

    def __str__(self):
        return f"BETWEEN {self.value1} AND {self.value2}"

class IS_NULL(LiteQLOperation):
    """Value is null"""
    def __str__(self):
        return "IS NULL"

class IS_NOT_NULL(LiteQLOperation):
    """Value is not null"""
    def __str__(self):
        return "IS NOT NULL"

class OR(LiteQLOperation):
    """The OR operator for multiple values
    
    Args:
        *values: Values to compare
        **columns: Columns to compare between different columns

    Examples:
        >>> table.find_one(name=OR("John", "Jane"))
        >>> table.find_one(OR(name="John", surname="Smith"))
    """

    _dont = True
    def __init__(self, *values, **columns):
        self.values = values
        self.columns = columns

    def __str__(self):
        key = getattr(self, "_key") if self.values else None

        values = f"({" OR ".join([_match_condition(key, val) for val in self.values])})" if self.values else None
        columns = f"({" OR ".join([_match_condition(k, self.columns[k]) for k in self.columns])})" if self.columns else None

        return values or columns