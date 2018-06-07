import prodigy
from multiprocessing import Process
from time import sleep
import atexit
from pathlib import Path

from prodigy.components import printers
from prodigy.components.loaders import get_stream
from prodigy.core import recipe, recipe_args
from prodigy.util import TASK_HASH_ATTR, log
from prodigy.components.preprocess import add_tokens
from datetime import datetime
from pymongo import MongoClient
import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from random import shuffle

# Config:
# - add list of coders
# - ?? add port per coder?
# - base file name for files
# - recipe, db, model, output

import spacy
nlp = spacy.blank("en")

def setup_mongo(collection_name, db_name = "gsr"):
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    coll = db[collection_name]
    return coll

class DBStream:
    """Certain parameters are hard coded, for instance the number of 
    annotaters to see each example and the Mongo DB name."""
    def __init__(self, active_coder, collection_name):
        self.active_coder = active_coder
        self.coll = setup_mongo(collection_name)
        print("Total tasks in collection: ", self.coll.count())

    def get_examples(self):
        print("get_examples called")
        examples = self.coll.find({"$and" : [
            {"seen" : {"$in" : [0,1,2,3]}},  
            {"coders" :  {"$nin" : [self.active_coder]}}]}).sort("seen", pymongo.DESCENDING).limit(200)
        examples = list(examples)
        print("inside get_examples, this many examples:", len(examples))
        for i in examples:
            if '_id' in i.keys():
                i['_id'] = str(i['_id'])
        shuffle(examples)  # this, of course, obviates the sorting a few lines above...
        self.examples = iter(examples)


# This decorator has ideas about what keyword arguments to take in.
# Repurpose some of these to convey other information, which is a bit
# ugly.
@prodigy.recipe('manual_custom',
        dataset=recipe_args['dataset'],
        source=recipe_args['source'], # use this slot for the coder name
        api=recipe_args['api'], # use this one for the collection name
        loader=recipe_args['loader'],
        label=recipe_args['label'],
        view_id=recipe_args['view'],
        memorize=recipe_args['memorize'],
        exclude=recipe_args['exclude'])
def manual_custom(dataset, source=None, view_id=None, label='', api=None,
         loader=None, memorize=False, exclude=None):
    """
    Click through pre-prepared examples, with no model in the loop.
    """

    log('RECIPE: Starting recipe mark', locals())
    coder = source # repurposing input slot
    stream_empty = iter([])
    stream = DBStream(coder, api) # using the api slot for collection name
    stream.get_examples()

    def ask_questions(stream):
        for eg in stream.examples:
            eg['time_loaded'] = datetime.now().isoformat()
            eg['mongo_collection'] = api # record where it came from
            # not serializeable
            eg['_id'] = str(eg['_id'])
            # add tokens. add_tokens expects a list...
            ts = add_tokens(nlp, [eg])
            #...and returns a generator
            eg = next(ts)
            yield eg


    def recv_answers(answers):
        for eg in answers:
            # Retrieve the example from the DB again to get most up-to-date
            # list of coders 
            updated_ex = list(stream.coll.find({'_id': ObjectId(eg['_id'])}))
            try:
                curr_cod = updated_ex[0]['coders']
            except KeyError:
                curr_cod = []
            # add current coder to the list
            curr_cod.append(coder)
            stream.coll.update_one({"_id": ObjectId(eg['_id'])}, # convert back
                                   {"$set": {"coders": curr_cod,
                                             "seen" : len(curr_cod)}})
            eg['time_returned'] = datetime.now().isoformat() # record submission time
            eg['active_coder'] = coder
            eg['coders'] = curr_cod


    def get_progress(session=0, total=0, loss=0):
        return None
        #done = stream.coll.count({"$or" : [
        #   {"coders"  : coder},
        #   {"seen" :  {"$gte": 3}}]})
        #total = stream.coll.count()
        #progress = done / total
        #return progress

    return {
        'view_id': view_id,
        'dataset': dataset,
        'stream': ask_questions(stream),
        'exclude': exclude,
        'progress' : get_progress,
        'update': recv_answers,
    }



class MultiProdigy:
    """These are functions that remain the same regardless of the view ID."""
    def __init__(self, coder_list, collection, dataset, view_id = None, label = None):
        self.coder_list = coder_list
        self.collection = collection
        self.dataset = dataset
        self.processes = []
        self.view_id = view_id
        self.label = label 

    def start_prodigies(self):
        print("Starting Prodigy processes...")
        for p in self.processes:
            p.start()
            sleep(1)

    def kill_prodigies(self):
        # Make sure all processes are killed on close
        print("Killing Prodigy threads")
        for i in self.processes:
            try:
                i.terminate()
            except AttributeError:
                print("Process {0} doesn't exist?".format(i))
        self.processes = []


class MultiProdigyManual(MultiProdigy):
   # There are two functions
    def serve(self, coder, port):
        print(coder)
        prodigy.serve('manual_custom',       # recipe
                      self.dataset,  # dataset to save it in
                      coder, # input file, repurposed for coder
                      "ner_manual", # view ID
                      self.label,
                      self.collection, # api, repurposed to be collection
                      None, # loader
                      True, # memorize
                      None, # exclude
                      port=port)  # port

    def make_prodigies(self):
        for coder_info in enumerate(self.coder_list):
            coder_info = coder_info[1] # wut
            thread = Process(target=self.serve, args = 
                    (coder_info['name'], 
                     coder_info['port']))
            self.processes.append(thread)



if __name__ == "__main__":
    mp = MultiProdigyManual(
            dataset = "apsa_tmp",
            coder_list = [{"name": "Andy", "port" : "9011"}],
        collection = "silver_assault")
    atexit.register(mp.kill_prodigies)
    mp.make_prodigies()
    mp.start_prodigies()
    while True:
        sleep(60 * 60)
        print("Restarting Prodigy...")
        mp.kill_prodigies()
        mp.make_prodigies()
        mp.start_prodigies()

