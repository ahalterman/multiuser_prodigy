import prodigy
from multiprocessing import Process
from time import sleep
from prodigy.recipes.ner import batch_train
import atexit

def serve_ner(ner_label, port):
    print(ner_label)
    filename = "data/{0}.jsonl".format(ner_label)
    prodigy.serve('ner.teach', "multiuser_test", "en_core_web_sm",
                  filename,  None, None, ner_label, port=port)

def make_prodigies(tag_list):
    all_threads = []
    for n, tag in enumerate(tag_list):
        thread =  Process(target=serve_ner, args=(tag, 9010 + n))
        all_threads.append(thread)
    return all_threads

def start_prodigies(process_list):
    for p in process_list:
        p.start()
        sleep(2)

def kill_prodigies(all_procs):
    print("Killing Prodigy threads")
    [i.terminate() for i in all_procs]

def train_ner():
    batch_train(dataset="multiuser_test",
                input_model="en_core_web_sm",
                n_iter = 5,
                output_model = "trained_ner/")



if __name__ == "__main__":
    all_procs = []
    atexit.register(kill_prodigies, all_procs = all_procs)
    print("Starting Prodigy processes...")
    all_procs = make_prodigies(["LOC", "PERSON", "GPE"])
    start_prodigies(all_procs)
    print(all_procs)
    while True:
        pass
