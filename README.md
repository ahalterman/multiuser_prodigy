# multiuser_prodigy

This is a bare-bones multi-annotator setup for [Prodigy](http://prodi.gy/),
Explosion AI's data annotation tool. Real multi-annotator support is [in the
works](https://support.prodi.gy/t/prodigy-roadmap/32), so this is just a
temporary solution until then.

This code is hard coded for annotators working on training an NER model but
could easily be modified for other tasks. Each NER tag is assigned to a different
instance of Prodigy running on a separate port and managed as Python
subprocess. Each annotator works on the Prodigy/port assigned to them.

Once a day, the main process batch updates the NER model and redeploys all the
Prodigy instances with the new model.

This is a pretty hacky and one-off solution, but comments and issues are
welcome!

## Mongo database

This code now supports assigning tasks from a central Mongo database rather
than from individual files.

You can start a Mongo DB in a Docker container:

```
sudo docker run -d -p 127.0.0.1:27017:27017 -v /home/andy/MIT/multiuser_prodigy/db:/data/db  mongo
```

To load a list of tasks into the database:

```
python mongo_load.py -i assault_not_assault.jsonl -c "assault_gsr"
```

where `-i` is a JSONL file of tasks and `-c` specifies the collection name to
load them into.

"seen" : {"$in" : [0,1]}},
            {"coders"

## Running

You'll need to modify the code of `multiuser_db.py` to access the right
collection, set the names/ports of annotators, and the desired interface (NER,
classification, etc).

Then you should launch the processes either in a `screen` or in the background:

```
python multiuser_db.py
```

## Analysis

`Report.Rmd` is an RMarkdown file that reads in a CSV of coding information and
generates figures in an HTML page that can be served from the annotation
server. To record information about how long each task takes, add something
like `eg['time_loaded'] = datetime.now().isoformat()` to your stream code and
something like `eg['time_returned'] = datetime.now().isoformat()` to your
update code. `report_maker.py` exports the DB to CSV and knits the RMarkdown on
that CSV.
