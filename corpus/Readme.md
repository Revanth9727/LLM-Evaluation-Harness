# Corpus

The corpus is the document store used to build `context[]` for datasets that do not embed context (e.g., `data/regression.jsonl`).

It enables:
1) Oracle-from-corpus evaluation (build context from gold `sources[]`)
2) Future RAG evaluation (retrieve context at runtime)

## Directory convention (required)
Store plain UTF-8 text per document page:

corpus/
  <DOC_ID>/
    1.txt
    2.txt
    3.txt
    ...

Where:
- `<DOC_ID>` matches `sources[].doc_id` in the dataset
- filenames are page numbers (integers)

Example:
- `corpus/HOLLM/80.txt`

## Page numbering
Use the PDF page index as extracted (1-based filenames).
Do NOT renumber files to match printed/book page numbers.

If a dataset uses a page offset mapping (e.g., HOLLM), the harness applies it at runtime.

## Blank pages
If a page has no extracted text, the file must contain exactly:

[[BLANK_PAGE]]

## Expected harness behavior (oracle mode)
For each dataset source `(doc_id, dataset_page)`:
- compute `corpus_page = dataset_page + page_offset` (if configured)
- load `corpus/<doc_id>/<corpus_page>.txt`
- emit a context chunk with header using the **dataset page**:
  `[<DOC_ID> p<DATASET_PAGE>]`
  followed by the loaded text

This keeps citations stable and validates against `sources[]`.

