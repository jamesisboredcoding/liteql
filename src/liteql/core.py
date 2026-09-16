import sqlite3
import json

from urllib.parse import urlparse, unquote
from typing import Dict, List

from .dialects import _dialect, SQLITE
from .errors import LiteQLConnectionError, LiteQLQueryError
from .attributes import LiteQLDatatype
from .operations import _match_condition, LiteQLOperation

class LiteQLQueryResult:
    """Result object for the SQL query"""
    def __init__(self, tuple: tuple, columns: list, _metadata: dict | None):
        self.result = {}
        self.metadata = _metadata or {}

        for idx, col in enumerate(columns):
            self.result[col] = tuple[idx]

    def __str__(self):
        return json.dumps(self.result, indent=2)

    def __repr__(self):
        return json.dumps(self.result, indent=2)

    def __getattr__(self, name):
        return self.metadata.get(name) or self.result.get(name)

    def __getitem__(self, key):
        return self.result.get(key)

class LiteQLTable:
    """LiteQL table object"""
    def __init__(self, db: LiteQL, name: str, schema: dict):
        self.db = db
        self.name = name
        self.schema = schema
        self.str_schema = {}

        for key in self.schema.keys():
            self.str_schema[key] = " ".join(str(attr) for attr in self.schema[key])

    def __repr__(self):
        return json.dumps(self.str_schema, indent=2)

    def __str__(self):
        return json.dumps(self.str_schema, indent=2)

    def drop(self):
        """Drops the table from the database
        WARNING: Dropping the table is **NOT UNDOABLE**, do so at your own risk
        """

    def insert(self, **fields) -> sqlite3.Cursor:
        """Inserts new row into table with specified data
        
        Args:
            **fields: Keys represent columns and values represent their values

        Example:
            >>> users_table.insert(name="John", email="john.doe@gmail.com")
            sqlite3.Cursor
        """

        try:
            sql = f"INSERT INTO {self.name} ({', '.join(fields.keys())}) VALUES ({', '.join(['?'] * len(fields))})"
            result = self.db.run(sql, tuple(fields.values()))
            return result
        except sqlite3.OperationalError as err:
            raise LiteQLQueryError(err)

    def update(self, conditions: List[LiteQLOperation] | None = None, allow_all: bool | None = False, **sets) -> Dict[str, int]:
        """Updates row in table with optionally specified conditions
        
        Args:
            conditions: List of LiteQLOperation conditions
            allow_all: Allow to affect all rows if no conditions are passed (**DANGEROUS**)
            **sets: Keys represent columns and values represent their values to update to

        Example:
            >>> users_table.update(conditions=[RAW(name="John")], income=2500)
            1
        """

        updates = []
        where_str = self._build_conditions(conditions, allow_all)

        for key in sets:
            val = sets[key]
            match val:
                case str(): updates.append(f"{key} = '{val}'")
                case int(): updates.append(f"{key} = {val}")
                case float(): updates.append(f"{key} = {val}")
                case LiteQLDatatype(): updates.append(f"{key} = {val.value}")

        update_sets = ", ".join(updates)
        try:
            sql = f"UPDATE {self.name} SET {update_sets} {where_str if conditions else ""}"
            result = self.db.run(sql)

            return {
                "lastrowid": result.lastrowid,
                "rowcount": result.rowcount
            }
        except sqlite3.OperationalError as err:
            raise LiteQLQueryError(err)

    def delete(self, conditions: List[LiteQLOperation] | None = None, allow_all: bool | None = False) -> Dict[str, int]:
        where_str = self._build_conditions(conditions, allow_all)
        try:
            sql = f"DELETE FROM {self.name} {where_str if conditions else ""}"
            result = self.db.run(sql)

            return {
                "lastrowid": result.lastrowid,
                "rowcount": result.rowcount
            }
        except sqlite3.OperationalError as err:
            raise LiteQLQueryError(err)

    def _build_conditions(self, conditions, allow_all):
        cds = []
        where_str = "WHERE"

        if conditions:
            for condition in conditions:
                if isinstance(condition, LiteQLOperation):
                    cds.append(str(condition))
        else:
            if not allow_all:
                raise LiteQLQueryError("Cannot affect rows without condition while allow_all is disabled")

        joined = " AND ".join(cds)
        where_str += " " + joined

        return where_str

    def _build_select(self, select, cds, **where):
        where_str = "WHERE"
        conditions = []

        for key in where:
            condition = where[key]
            conditions.append(_match_condition(key, condition))

        if cds:
            for condition in cds:
                if isinstance(condition, LiteQLOperation):
                    conditions.append(str(condition))

        joined = " AND ".join(conditions)
        where_str += " " + joined

        sql = f"SELECT {"*" if not select else ", ".join(select)} FROM {self.name} {where_str if where or cds else ""}"
        return sql

    def find_one(self, select: None | list = None, conditions: List[LiteQLOperation] | None = None, **where) -> LiteQLQueryResult | None:
        """Runs a SELECT SQL query with query paramaters and returns one result
        
        Args:
            select: List of columns to retrieve
            conditions: LiteQLCondition objects
            **where: Keys represent columns and valeus represent their values

        Example:
            >>> from liteql.operations import BETWEEN
            >>> from datetime import date
            >>> users_table.find_one(name="Jane", date_of_birth=BETWEEN(date(1987, 05, 24), date(2002, 11, 03)))
            1
        """

        try:
            sql = self._build_select(select, conditions, **where)
            cursor = self.db.run(sql)

            return LiteQLQueryResult(cursor.fetchone(), self.schema.keys(), {
                "lastrowid": cursor.lastrowid,
                "rowcount": cursor.rowcount
            })
        except sqlite3.OperationalError as err:
            raise LiteQLQueryError(err)

    def find_many(self, select: None | list = None, conditions: List[LiteQLOperation] | None = None, **where) -> List[LiteQLQueryResult | None]:
        """Runs a SELECT SQL query with query paramaters and returns all matching results
        
        Args:
            select: List of columns to retrieve
            conditions: LiteQLCondition objects
            **where: Keys represent columns and valeus represent their values

        Example:
            >>> from liteql.operations import BETWEEN
            >>> from datetime import date
            >>> users_table.find_many(name="Jane", date_of_birth=BETWEEN(date(1987, 05, 24), date(2002, 11, 03)))
            1
        """

        try:
            sql = self._build_select(select, conditions, **where)
            cursor = self.db.run(sql)

            return [LiteQLQueryResult(result, self.schema.keys(), {
                "lastrowid": cursor.lastrowid,
                "rowcount": cursor.rowcount
            }) for result in cursor.fetchall()]
        except sqlite3.OperationalError as err:
            raise LiteQLQueryError(err)

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
        self.tables = {}

    def _parse_dialect(self):
        if "://" not in self.url:
            self.path = self.url
            return SQLITE

        u = urlparse(self.url)
        try:
            dialect = _dialect(u.scheme)
        except ValueError:
            raise LiteQLConnectionError(f"Unsupported database: {u.scheme}")

        if dialect is SQLITE:
            self.path = u.path[1:]
            return dialect

        self.user = unquote(u.username or "")
        self.password = unquote(u.password or "")
        self.host = u.hostname or "localhost"
        self.port = u.port or 3306
        self.database = u.path.lstrip("/")
        return dialect

    def connect(self, timeout: int = 5, **kwargs):
        """Connects to the SQLite/MySQL database
        
        Args:
            timeout: Amount of seconds to wait before giving up
            **kwargs: Additional optional sqlite3.connect arguments

        Example:
            >>> db.connect(3)
            1
        """

        if self.connection:
            raise LiteQLConnectionError("Already connected to database")
        try:
            self.connection = sqlite3.connect(self.path, timeout=timeout, **kwargs)
        except sqlite3.DatabaseError as err:
            raise err

    def disconnect(self):
        """Disconnects from the SQLite/MySQL database

        Example:
            >>> db.disconnect()
            1
        """
        
        try:
            self.connection.close()
        except sqlite3.DatabaseError as err:
            raise err

    def run(self, sql: str, params = ()) -> sqlite3.Cursor:
        """Runs a SQL query on the connected database
        
        Args:
            sql: The SQL query to run
            params: The prepared statement params when using "?"

        Example:
            >>> db.run("SELECT * FROM users")
            sqlite3.Cursor
        """

        if not self.connection:
            raise LiteQLQueryError("Not connected to database")
        try:
            cursor = self.connection.cursor()
            cursor = cursor.execute(sql, params)

            self.connection.commit()
            return cursor
        except sqlite3.ProgrammingError as err:
            raise LiteQLQueryError(f"Failed to execute SQL query")

    def create_table(self, table_name: str, table_schema: Dict[str, List[LiteQLDatatype]]) -> LiteQLTable:
        """Creates a new table in the connecte database if doesn't already exists, adds new columns if new keys are added
        
        Args:
            table_name: The name of the table
            table_schema: Dictionary containing keys as column names and values with list of LiteQLDatatype and LiteQLAttribute objects

        Example:
            >>> db.create_table("users", {
            >>>     "id": [INT(), PRIMARY_KEY()],
            >>>     "name": [VARCHAR(), NOTNULL()],
            >>> })
            1
        """

        if not self.connection:
            raise LiteQLQueryError("Not connected to database")
        for ls in table_schema.values():
            for attr in ls:
                attr.dialect = self.dialect

        try:
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({", ".join([
                key + " " + " ".join(str(attr) for attr in table_schema[key]) for key in table_schema.keys()
            ])})"
    
            self.run(sql)
    
            cols = table_schema.keys()
            current_cols = [
                col[1] for col in self.run(f"PRAGMA table_info({table_name})").fetchall()
            ]
    
            new_cols = [col for col in cols if not col in current_cols]
            if new_cols:
                for new_col in new_cols:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {new_col} {" ".join(str(attr) for attr in table_schema[new_col])}"
                    print(sql)
                    self.run(sql)
        except sqlite3.OperationalError as err:
            raise LiteQLQueryError(err)

        self.tables[table_name] = LiteQLTable(self, table_name, table_schema)
        return self.tables[table_name]