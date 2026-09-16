from liteql import LiteQL
from liteql.attributes import *
from liteql.operations import *

db = LiteQL("app.db")
db.connect()

users = db.create_table("users", {
    "id": [INT(), PRIMARY_KEY()],
    "name": [VARCHAR(), NOTNULL()],
    "email": [VARCHAR(), NOTNULL()],
    "income": [INT()]
})

users.update(conditions=[RAW(name="John")], email="Specified", income=2500)
print(users.find_many())