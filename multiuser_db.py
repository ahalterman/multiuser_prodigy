import prodigy
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

from custom_recipes import manual_custom
# Config:
# - add list of coders
# - ?? add port per coder?
# - base file name for files
# - recipe, db, model, output

class MultiProdigy:
    def __init__(self,
                 coder_list,
                 db_name,
                 collection_name,
                 recipe_name,
                 view_id,
                 dataset,
                 label=None,
                 model="blank:en"):
        self.coder_list = coder_list
        self.dataset = dataset,
        self.db_name = db_name,
        self.collection_name = collection_name
        self.processes = []
        self.recipe_name=recipe_name
        self.view_id=view_id
        self.label=label
        self.model=model
        self.label=label

        print("Using recipe ", self.recipe_name)
        
    def serve(self, coder, port):
        print(coder)
        prodigy.serve(self.recipe_name,
                      self.dataset,
                      self.model,
                      coder, 
                      self.collection_name,
                      self.db_name,
                      self.label,
                      #view_id=self.view_id, 
                      #label=self.label,
                      #None, # api
                      #None, # loader
                      #True, # memorize
                      #None, # exclude
                      port=port,
                      )  # port

    def make_prodigies(self):
        for coder_info in enumerate(self.coder_list):
            coder_info = coder_info[1] # wut
            thread = Process(target=self.serve, kwargs =
                    {"coder": coder_info['name'], 
                        "port": coder_info['port']})
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
    mp = MultiProdigy(coder_list = [{"name" : "Andy", "port" : 9010},
                                    {"name" : "Jill", "port" : 9011}],
                      db_name = "gsr",
                      collection_name = "protest_apsa_en_prod",
                      recipe_name="manual_custom",
                      view_id="manual_custom",
                      dataset="tmp_apsa",
                      label="NOUN,OBJ")
    atexit.register(mp.kill_prodigies)
    mp.make_prodigies()
    mp.start_prodigies()
    while True:
        sleep(30 * 60)
        print("Restarting Prodigy...")
        mp.kill_prodigies()
        mp.make_prodigies()
        mp.start_prodigies()

    #    if datetime.datetime.now() > mp.retrain_time:
    #        print("Retraining model and scheduling next retraining for tomorrow")
    #        mp.make_retrain_time() # bump to tomorrow
    #        mp.train_and_restart()

