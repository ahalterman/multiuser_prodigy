import prodigy
from multiprocessing import Process
from time import sleep
from prodigy.recipes.ner import batch_train
import atexit
from pathlib import Path

class MultiProdigy:
    def __init__(self, tag_list = ["LOC", "GPE", "PERSON"]):
        self.tag_list = tag_list
        self.processes = []

    def serve_ner(self, ner_label, port):
        print(ner_label)
        # We can actually give everyone the same document. That'll simplify the
        # directory and the update process, any may help the training process.
        filename = "data/{0}.jsonl".format(ner_label)
        prodigy.serve('ner.teach', "multiuser_test", "trained_ner",
                      filename,  None, None, ner_label, None, "multiuser_test",
                      port=port)

    def make_prodigies(self):
        for n, tag in enumerate(self.tag_list):
            thread =  Process(target=self.serve_ner, args=(tag, 9010 + n))
            self.processes.append(thread)

    def start_prodigies(self):
        print("Starting Prodigy processes...")
        for p in self.processes:
            p.start()
            sleep(2)

    def kill_prodigies(self):
        print("Killing Prodigy threads")
        [i.terminate() for i in self.processes]

    def train_and_restart(self):
        print("Re-training model with new annotations...")
        batch_train(dataset="multiuser_test",
                    input_model="en_core_web_sm",
                    n_iter = 5,
                    output_model = Path("/Users/ahalterman/MIT/NSF_RIDIR/multiuser_prodigy/ner_trained"))
        print("Model training complete. Restarting service with new model...")
        self.kill_prodigies()
        self.make_prodigies()
        self.start_prodigies()

if __name__ == "__main__":
    mp = MultiProdigy()
    atexit.register(mp.kill_prodigies)
    mp.make_prodigies()
    mp.start_prodigies()
    while True:
        sleep(10)
        mp.train_and_restart()
        pass
