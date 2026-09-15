import sqlite3

from urllib.parse import urlparse, unquote

from .dialects import _dialect, SQLITE
from .errors import LiteQLConnectionError, LiteQLQueryError

class LiteQL:
    """Connection wrapper for SQLite and MySQL

    Args:
        url: Database URL, e.g: "sqlite:///app.db" or "mysql://user:password@host/db". A bare path means SQLite.

    Example:
        >>> db = LiteQL("app.db")
        >>> db.insert("users", name="John")
        1
    """

    def __init__(self, url: str):
        self.url = url
        self.dialect = self._parse_dialect()
        self.connection = None

    def _parse_dialect(self):
        if "://" not in self.url:
            self.path = self.url
            return SQLITE

        u = urlparse(self.url)
        try:
            dialect = _dialect(u.scheme)
        except ValueError:
            raise LiteQLConnectionError(f"Unsupported databse: {u.schema}")

        if dialect is SQLITE:
            self.path = u.path[1:]
            return dialect

        self.user = unquote(u.username or "")
        self.password = unquote(u.password or "")
        self.host = u.hostname or "localhost"
        self.port = u.port or 3306
        self.database = u.path.lstrip("/")
        return dialect

    def connect(self, timeout: int = 5):
        """Connects to the SQLite/MySQL database
        
        Args:
            timeout: Amount of seconds to wait before giving up

        Examples:
            >>> db.connect(3)
            1
        """

        if self.connection:
            raise LiteQLConnectionError("Already connected to database")
        try:
            self.connection = sqlite3.connect(self.path, timeout=timeout)
        except sqlite3.DatabaseError as err:
            raise err

    def disconnect(self):
        """Disconnects from the SQLite/MySQL database

        Examples:
            >>> db.disconnect()
            1
        """
        
        try:
            self.connection.close()
        except sqlite3.DatabaseError as err:
            raise err

    def run(self, sql: str, params = ()):
        if not self.connection:
            raise  LiteQLQueryError("Not connected to database")
        try:
            return self.connection.execute(sql, params)
        except sqlite3.ProgrammingError as err:
            raise LiteQLQueryError(f"Failed to execute SQL query")

    def create_table(self, table_name: str, table_schema: dict):
        if not self.connection:
            raise  LiteQLQueryError("Not connected to database")
        for ls in table_schema.values():
            for attr in ls:
                attr.dialect = self.dialect
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({",".join([
            key + " " + " ".join(str(attr) for attr in table_schema[key]) for key in table_schema.keys()
        ])})"
        print(sql)