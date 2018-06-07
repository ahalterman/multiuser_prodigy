import prodigy
from multiprocessing import Process
from time import sleep
from prodigy.recipes.ner import batch_train
import atexit
from pathlib import Path
import datetime as dt

class MultiProdigy:
    def __init__(self, tag_list = ["LOC", "GPE", "PERSON", "ORG", "DATE", "NORP"]):
        self.tag_list = tag_list
        self.processes = []

    def serve_ner(self, ner_label, port):
        print(ner_label)
        # We can actually give everyone the same document. That'll simplify the
        # directory and the update process, any may help the training process.
        #filename = "data/{0}.jsonl".format(ner_label)
        filename = "data/aljazeera_1.jsonl"
        prodigy.serve('ner.teach', "arabic_ner_db", "model-final",
                      filename,  None, None, ner_label, None, "arabic_ner_db",
                      port=port)

    def serve_ner_manual(self, ner_label, port):
        print(ner_label)
        # We can actually give everyone the same document. That'll simplify the
        # directory and the update process, any may help the training process.
        #filename = "data/{0}.jsonl".format(ner_label)
        filename = "data/aljazeera_1.jsonl"
        prodigy.serve('ner.manual', "arabic_ner_db", "arabic_model",
                      filename,  None, None, ner_label, "arabic_ner_db",
                      port=port)


    def make_prodigies(self):
        for n, tag in enumerate(self.tag_list):
            thread =  Process(target=self.serve_ner_manual, args=(tag, 9010 + n))
            #thread =  Process(target=self.serve_ner, args=(tag, 9010 + n))
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

    def train_and_restart(self):
        print("Re-training model with new annotations...")
        batch_train(dataset="arabic_ner_db",
                    input_model="model-final",
                    n_iter = 10,
                    output_model = Path("arabic_model_updated"))
        print("Model training complete. Restarting service with new model...")
        self.kill_prodigies()
        self.make_prodigies()
        self.start_prodigies()

    def make_retrain_time(self):
        # make a datetime for tomorrow at 4 am
        tomorrow = dt.datetime.today() + dt.timedelta(days=1)
        self.retrain_time = dt.datetime.combine(tomorrow, dt.time(4, 0))


if __name__ == "__main__":
    mp = MultiProdigy()
    mp.make_retrain_time()
    atexit.register(mp.kill_prodigies)
    mp.make_prodigies()
    mp.start_prodigies()
    while True:
        sleep(5)
        if dt.datetime.now() > mp.retrain_time:
            print("Retraining model and scheduling next retraining for tomorrow")
            mp.make_retrain_time() # bump to tomorrow
            mp.train_and_restart()
