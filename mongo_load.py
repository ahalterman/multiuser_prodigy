import jsonlines
from pymongo import MongoClient
import plac

@plac.annotations(
    input_file=("JSONL of tasks to load", "option", "i", str),
    coll_name=("Collectionto load into", "option", "c", str),
    db_name=("Database to load into", "option", "d", str))
def load(input_file, coll_name, db_name = "gsr"):
    # quick script for updating Mongo tasks
    with jsonlines.open(input_file, "r") as f:
        to_load = list(f.iter())
    print("Loading into db {0}, collection {1}".format(db_name, coll_name))
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    coll = db[coll_name]
    print("Before loading:", coll.count())
    coll.insert_many(to_load)
    print("After loading:", coll.count())

if __name__ == "__main__":
    plac.call(load)
