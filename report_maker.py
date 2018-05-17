import prodigy
from prodigy.components.db import connect
from pandas import DataFrame
from datetime import datetime, timedelta
from dateutil import parser
import os

db = connect()

examples = db.get_dataset("gsr_is_protest")

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
df.to_csv("coding_summary.csv")
os.system("""Rscript -e 'library(rmarkdown); rmarkdown::render("Report.Rmd", "html_document")'""")

