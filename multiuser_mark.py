import prodigy
from multiprocessing import Process
from time import sleep
from prodigy.recipes.ner import batch_train
import atexit
from pathlib import Path
import datetime as dt

from prodigy.components import printers
from prodigy.components.loaders import get_stream
from prodigy.core import recipe, recipe_args
from prodigy.util import TASK_HASH_ATTR, log
from datetime import datetime
from collections import Counter

# It's all going to be run by coder name.

# Config:
# - add list of coders
# - ?? add port per coder?
# - base file name for files
# - recipe, db, model, output

@prodigy.recipe('mark_custom',
        dataset=recipe_args['dataset'],
        source=recipe_args['source'],
        api=recipe_args['api'],
        loader=recipe_args['loader'],
        label=recipe_args['label'],
        view_id=recipe_args['view'],
        memorize=recipe_args['memorize'],
        exclude=recipe_args['exclude'])
def mark_custom(dataset, source=None, view_id=None, label='', api=None,
         loader=None, memorize=False, exclude=None):
    """
    Click through pre-prepared examples, with no model in the loop.
    """
    log('RECIPE: Starting recipe mark', locals())
    stream = list(get_stream(source, api, loader))

    counts = Counter()
    memory = {}

    def fill_memory(ctrl):
        if memorize:
            examples = ctrl.db.get_dataset(dataset)
            log("RECIPE: Add {} examples from dataset '{}' to memory"
                .format(len(examples), dataset))
            for eg in examples:
                memory[eg[TASK_HASH_ATTR]] = eg['answer']

    def ask_questions(stream):
        for eg in stream:
            eg['time_loaded'] = datetime.now().isoformat()
            if TASK_HASH_ATTR in eg and eg[TASK_HASH_ATTR] in memory:
                answer = memory[eg[TASK_HASH_ATTR]]
                counts[answer] += 1
            else:
                if label:
                    eg['label'] = label
                yield eg

    def recv_answers(answers):
        for eg in answers:
            counts[eg['answer']] += 1
            memory[eg[TASK_HASH_ATTR]] = eg['answer']
            eg['time_returned'] = datetime.now().isoformat()

    def print_results(ctrl):
        print(printers.answers(counts))

    def get_progress(session=0, total=0, loss=0):
        progress = len(counts) / len(stream)
        return progress

    return {
        'view_id': view_id,
        'dataset': dataset,
        'stream': ask_questions(stream),
        'exclude': exclude,
        'update': recv_answers,
        'on_load': fill_memory,
        'on_exit': print_results,
        'config': {'label': label}
    }

class MultiProdigy:
    def __init__(self,
        coder_list = [{"name" : "Daniel", "port" : 9010},
                       {"name" : "Youseff", "port" : 9011},
                       {"name" : "Emad", "port" : 9012},
                       {"name" : "Rafeef", "port" : 9013},
                       {"name" : "Mahmoud", "port" : 9014},
                       {"name" : "Zach", "port" : 9015},
                       {"name" : "Collin", "port" : 9016},
                      ]):
        self.coder_list = coder_list
        self.processes = []

    def serve(self, coder, port):
        print(coder)
        base = "data/protest_for_classification_"
        filename = "{0}{1}.jsonl".format(base, coder)
        prodigy.serve('mark_custom',       # recipe
                      "gsr_is_protest",  # db
                      filename, # input file
                      "classification", # view ID
                      "PROTEST",
                      None, # api
                      None, # loader
                      True, # memorize
                      "gsr_is_protest", # exclude
                      port=port)  # port

    def make_prodigies(self):
        for coder_info in enumerate(self.coder_list):
            coder_info = coder_info[1] # wut
            thread =  Process(target=self.serve, args = (coder_info['name'], coder_info['port']))
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
    #mp.make_retrain_time()
    atexit.register(mp.kill_prodigies)
    mp.make_prodigies()
    mp.start_prodigies()
    while True:
        sleep(5)
    #    if dt.datetime.now() > mp.retrain_time:
    #        print("Retraining model and scheduling next retraining for tomorrow")
    #        mp.make_retrain_time() # bump to tomorrow
    #        mp.train_and_restart()

