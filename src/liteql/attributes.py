from .dialects import SQLITE, MYSQL

class INT:
    """32-bit integer"""
    def __init__(self, length: int = 9):
        self.length = length

    def __str__(self):
        return f"INT({self.length})" if self.dialect is MYSQL else "INTEGER"

    def __repr__(self):
        return "INT" if self.dialect is MYSQL else "INTEGER"

class AUTO_INCREMENT:
    """auto"""
    def __str__(self):
        return "AUTO_INCREMENT" if self.dialect is MYSQL else "AUTOINCREMENT"

    def __repr__(self):
        return "AUTO_INCREMENT" if self.dialect is MYSQL else "AUTOINCREMENT"