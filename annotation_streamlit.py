
import streamlit as st
import spacy
import base64
import pandas as pd
import jsonlines

from pymongo import MongoClient


HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def setup_mongo():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['gsr']
    coll = db['prod_dec_2020_2']
    return coll

def visualize(coll):
    coder = st.selectbox("Select your port/ID number",
              [9015, 9016, 9017, 9019, 9020, 9022, 9023, 9025])
    coder = int(coder)
    #st.markdown("Total sentences in collection: {}".format(coll.count()))
    assigned = coll.count({"assigned_annotators": {"$in" : [coder]}})
    completed = coll.count({"coders": {"$in" : [coder]}})
    st.markdown("Sentences assigned to {}: {}".format(coder, assigned))
    st.markdown("Sentences completed by {}: {}".format(coder, completed))
    st.markdown("Progress:")
    try:
        prog = completed/assigned
    except ZeroDivisionError:
        prog = 0
    st.progress(prog)


st.title('Annotation progress')
st.markdown("Check your annotation progress by selecting your port/ID number")
coll = setup_mongo()
visualize(coll)
