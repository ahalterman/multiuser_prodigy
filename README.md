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
