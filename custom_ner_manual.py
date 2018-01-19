import random
import mmh3
import json
import spacy
import copy

from .compare import get_questions as get_compare_questions
from ..models.ner import EntityRecognizer, merge_spans
from ..models.matcher import PatternMatcher
from ..components import printers
from ..components.db import connect
from ..components.preprocess import split_sentences, split_spans, split_tokens
from ..components.sorters import prefer_uncertain
from ..components.loaders import get_stream
from ..components.filters import filter_tasks
from ..core import recipe, recipe_args
from ..util import split_evals, get_labels, get_print, combine_models
from ..util import export_model_data, set_hashes, log, prints
from ..util import INPUT_HASH_ATTR, TASK_HASH_ATTR


DB = connect()

@recipe('ner.manual',
        dataset=recipe_args['dataset'],
        spacy_model=recipe_args['spacy_model'],
        source=recipe_args['source'],
        api=recipe_args['api'],
        loader=recipe_args['loader'],
        label=recipe_args['label'],
        exclude=recipe_args['exclude'])
def manual(dataset, spacy_model, source=None, api=None, loader=None,
           label=None, exclude=None):
    """
    Mark spans by token. Requires only a tokenizer and no entity recognizer,
    and doesn't do any active learning.
    """
    log("RECIPE: Starting recipe ner.manual", locals())
    nlp = spacy.load(spacy_model)
    log("RECIPE: Loaded model {}".format(spacy_model))
    labels = get_labels(label, nlp)
    log("RECIPE: Annotating with {} labels".format(len(labels)), labels)
    stream = get_stream(source, api=api, loader=loader, rehash=True,
                        dedup=True, input_key='text')
    stream = split_tokens(nlp, stream)

    return {
        'view_id': 'ner_manual',
        'dataset': dataset,
        'stream': stream,
        'exclude': exclude,
        'config': {'labels': labels}
    }

