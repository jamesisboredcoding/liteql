from .dialects import MYSQL

# Datatypes

class LiteQLDatatype:
    """SQL/SQLite datatype object"""

class INT(LiteQLDatatype):
    """32-bit integer"""
    def __init__(self, length: int = 9):
        self.length = length

    def __str__(self):
        return f"INT({self.length})" if self.dialect is MYSQL else "INTEGER"

    def __repr__(self):
        return "INT" if self.dialect is MYSQL else "INTEGER"

class PRIMARY_KEY(LiteQLDatatype):
    """Assigns key as the primary key"""
    def __str__(self):
        return "PRIMARY KEY"

    def __repr__(self):
        return "PRIMARY KEY"

class VARCHAR(LiteQLDatatype):
    """UTF-8 string characters"""
    def __init__(self, length: int = 255):
        self.length = length

    def __str__(self):
        return f"VARVHAR({self.length})" if self.dialect is MYSQL else "VARCHAR"

    def __repr__(self):
        return f"VARVHAR({self.length})" if self.dialect is MYSQL else "VARCHAR"

# Attributes

class AUTO_INCREMENT:
    """Auto increments integer value"""
    def __str__(self):
        return "AUTO_INCREMENT" if self.dialect is MYSQL else "AUTOINCREMENT"

    def __repr__(self):
        return "AUTO_INCREMENT" if self.dialect is MYSQL else "AUTOINCREMENT"

class NOTNULL:
    """Value cannot be NULL"""
    def __str__(self):
        return "NOT NULL"

    def __repr__(self):
        return "NOT NULL"