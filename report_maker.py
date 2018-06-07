import prodigy
from prodigy.components.db import connect
from pandas import DataFrame
from datetime import datetime, timedelta
from dateutil import parser
import os
import plac

@plac.annotations(
    db_name=("Name of Prodigy database to generate export from", "option", "i", str))
def main(db_name):
    db = connect()
    examples = db.get_dataset(db_name)
    print("Total examples: ", len(examples))
    
    diffs = []
    for ex in examples:
        if 'time_returned' in ex.keys() and 'time_loaded' in ex.keys():
            date = parser.parse(ex['time_returned']).strftime("%Y-%m-%d")
            diff = parser.parse(ex['time_returned']) - parser.parse(ex['time_loaded'])
            diff = diff.total_seconds()
            diffs.append({"date" : date,
                        "coder" : ex['active_coder'],
                        "diff" : diff,
                         "id" : ex['id'][-16:],
                         'answer': ex['answer']})
    
    df = DataFrame(diffs)
    df.to_csv("/home/andy/multiuser_prodigy/coding_summary.csv")
    os.system("""/usr/bin/Rscript -e 'library(rmarkdown); rmarkdown::render("multiuser_prodigy/Report.Rmd", "html_document")'""")
    os.system("""echo pwd""")

if __name__ == "__main__":
    plac.call(main)
