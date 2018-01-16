import prodigy
from multiprocessing import Process
from time import sleep
from prodigy.recipes.ner import batch_train
import atexit

def serve_ner(ner_label, port):
    print(ner_label)
    filename = "data/{0}.jsonl".format(ner_label)
    prodigy.serve('ner.teach', "multiuser_test", "en_core_web_sm",
                  filename, label = "LOC",
                  port=port)

def kill_prodigies():
    print("Killing Prodigy threads")
    loc_thread.terminate()
    gpe_thread.terminate()
    person_thread.terminate()

def train_ner():
    batch_train(dataset="multiuser_test",
                input_model="en_core_web_sm",
                n_iter = 5,
                output_model = "trained_ner/")

if __name__ == "__main__":
    atexit.register(kill_prodigies)
    print("Starting Prodigy processes...")
    loc_thread = Process(target=serve_ner, args=("LOC", "9017"))
    person_thread = Process(target=serve_ner, args=("PERSON", "9018"))
    gpe_thread = Process(target=serve_ner, args=("GPE", "9019"))
    loc_thread.start()
    sleep(3)
    person_thread.start()
    sleep(3)
    gpe_thread.start()
    while True:
        pass
