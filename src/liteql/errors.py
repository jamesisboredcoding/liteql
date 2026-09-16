class LiteQLError(Exception):
    """Base class for all LiteQL errors"""

class LiteQLConnectionError(LiteQLError):
    """Could not connect to database"""

class LiteQLQueryError(LiteQLError):
    """Query failed to execute"""

class LiteQLOperationError(LiteQLError):
    """Failed to execute an operation"""