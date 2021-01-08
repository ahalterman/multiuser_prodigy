import prodigy
import spacy
from multiprocessing import Process
from time import sleep
import atexit
from pathlib import Path

from prodigy.components import printers
from prodigy.components.loaders import get_stream
from prodigy.core import recipe, recipe_args
from prodigy.util import TASK_HASH_ATTR, log
from datetime import datetime
from pymongo import MongoClient
import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from random import shuffle


class DBStream:
    def __init__(self, active_coder, collection_name):
        print("Using collection: {}".format(collection_name))
        self.active_coder = active_coder
        self.coll = setup_mongo(collection_name)
        print("Total tasks in collection: ", self.coll.count_documents({}))

    def get_examples(self):
        print("get_examples called")
        examples = self.coll.find({"$and" : [
            {"assigned_annotators" : {"$in" : [self.active_coder]}}, # check if the task is assigned to the current coder...
            {"coders" :  {"$nin" : [self.active_coder]}}]}).sort("sent_id", pymongo.ASCENDING) # ...but the current coder hasn't seen it yet
        examples = list(examples)
        print("inside get_examples, this many examples:", len(examples))
        for i in examples:
            i['_id'] = str(i['_id']) # this gets created by mongo 
            i['_task_hash'] = hash(str(i['_id']) + str(self.active_coder))
            i['_input_hash'] = hash(str(i['_id']) + str(self.active_coder))
        self.examples = iter(examples)
        ## !! Need to prioritize examples with 2 or 1 views.

def setup_mongo(collection_name, db_name = "gsr"):
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    coll = db[collection_name]
    return coll

@prodigy.recipe('toi_blocks')
def toi_blocks(dataset, source=None, collection="prod_dec_2020_2"):
    log('RECIPE: Starting recipe mark', locals())
    coder = source # repurposing input slot
    print("Coder from within toi_blocks:", coder)
    stream_empty = iter([])
    stream = DBStream(coder, collection)
    stream.get_examples()
    #print("Initial number of examples in queue:", len(list(stream.examples)))
    #print("Initial examples in queue:", list(stream.examples))

    def ask_questions(stream_empty):
        #print("Hitting 'ask_question', with ", len(list(stream.examples)), " in the queue")
        #print(list(stream.examples))
        #print(stream.reced)
        for eg in stream.examples:
            #stream.get_examples()
            eg['time_loaded'] = datetime.now().isoformat()
            eg['active_coder'] = coder
            # not serializeable
            eg['_id'] = str(eg['_id'])
            yield eg


    #### Problem with the post-answer update.
    ## Not refreshing

    def recv_answers(answers):
        for eg in answers:
            print("Answer back: ", coder, datetime.now().isoformat())#, eg)
            # Get the example from the DB again in case it's changed
            updated_ex = list(stream.coll.find({'_id': ObjectId(eg['_id'])}))
            try:
                curr_cod = updated_ex[0]['coders']
            except KeyError:
                curr_cod = []
            # add current coder to the list
            curr_cod.append(coder)
            stream.coll.update_one({"_id": ObjectId(eg['_id'])}, # convert back
                                {"$set": {"coders": curr_cod,
                                         "seen" : len(curr_cod),
                                         'time_returned': datetime.now().isoformat(),
                                         'time_loaded': eg['time_loaded'],
                                         'active_coder': coder
                                         }})
            eg['time_returned'] = datetime.now().isoformat()
            eg['seen'] = len(curr_cod)

    def print_results(ctrl):
        print(printers.answers(counts))

    def get_progress(*args, **kwargs):
        done = stream.coll.count_documents({"coders"  : coder})
        total = stream.coll.count_documents({})
        return done / total

    # We can use the blocks to override certain config and content, and set
    # "text": None for the choice interface so it doesn't also render the text
    blocks = [
        {"view_id": "choice", "text": None},
        {"view_id": "text_input", "field_rows": 3, "field_label": "If you found this example difficult or ambiguous please explain why."}
      ]

    return {
        "dataset": dataset,          # the dataset to save annotations to
        "view_id": "blocks",         # set the view_id to "blocks"
        "stream": ask_questions(stream_empty),            # the stream of incoming examples
        "config": {
            "labels": ["RELEVANT"],  # the labels for the manual NER interface
            "blocks": blocks,         # add the blocks to the config
        },
        'update': recv_answers,
        #"custom_theme": {"cardMaxWidth": "90%"},
    }

#    return {
#        'view_id': view_id,
#        'dataset': dataset,
#        'stream': ask_questions(stream_empty),
#        'exclude': exclude,
#        "flag": True,
#        "custom_theme": {"cardMaxWidth": "90%"},
#        'progress' : get_progress,
#        'on_exit': print_results
#    }

class MultiProdigy:
    def __init__(self,
        coder_list = [#{"name" : "Andy", "port" : 9010},
                      # {"name" : "Katie", "port" : 9011},
                      # {"name" : "Sheikh", "port" : 9012},
                       #{"name" : 9014, "port" : 9014},
                       {"name" : 9015, "port" : 9015},
                       {"name" : 9016, "port" : 9016},
                       {"name" : 9017, "port" : 9017},
                       #{"name" : 9018, "port" : 9018},
                       {"name" : 9019, "port" : 9019},
                       {"name" : 9020, "port" : 9020},
                       #{"name" : 9021, "port" : 9021},
                       {"name" : 9022, "port" : 9022},
                       {"name" : 9023, "port" : 9023},
                       #{"name" : 9024, "port" : 9024},
                       {"name" : 9025, "port" : 9025},
                      ]):
        self.coder_list = coder_list
        self.processes = []

    def serve(self, coder, port):
        print(coder)
        #filename = "{0}{1}.jsonl".format(base, coder)
        prodigy.serve('toi_blocks',       # recipe
                      "prod_dec_2020_2",  # collection
                      coder, # input file, repurposed for coder
                      port=port)  # port

    def make_prodigies(self):
        for coder_info in enumerate(self.coder_list):
            coder_info = coder_info[1] # wut
            thread = Process(target=self.serve, args = (coder_info['name'], coder_info['port']))
            self.processes.append(thread)

    def start_prodigies(self):
        print("Starting Prodigy processes...")
        for p in self.processes:
            p.start()
            sleep(1)

    def kill_prodigies(self):
        print("Killing Prodigy threads")
        for i in self.processes:
            try:
                i.terminate()
            except AttributeError:
                print("Process {0} doesn't exist?".format(i))
        self.processes = []


if __name__ == "__main__":
    mp = MultiProdigy()
    atexit.register(mp.kill_prodigies)
    mp.make_prodigies()
    mp.start_prodigies()
    while True:
        sleep(60 * 60)
        print("Restarting Prodigy...")
        mp.kill_prodigies()
        mp.make_prodigies()
        mp.start_prodigies()


