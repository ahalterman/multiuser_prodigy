import jsonlines
from pymongo import MongoClient
import plac
import sys

@plac.annotations(
    coll_name=("Collectionto load into", "option", "c", str),
    db_name=("Database to load into", "option", "d", str))
def delete(coll_name, db_name = "gsr"):
    # quick script for updating Mongo tasks
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    coll = db[coll_name]
    count = coll.count()
    conf = input("You're about to delete the collection {0}, which has {1} records. Please type this name to confirm:  ".format(coll_name, count))
    if conf != coll_name:
        print("Bye!")
        sys.exit(0)
    if conf == coll_name:
        coll.delete_many({})
        print("Deleted all records from ", coll_name)

if __name__ == "__main__":
    plac.call(delete)
