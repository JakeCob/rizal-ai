# Corpus texts

The three editions of Noli Me Tangere that `rizalai ingest` and `rizalai bootstrap` read, committed so production passages are byte-identical to dev's (DECISIONS.md D37). Hand-aligned passage refs in content/ point at paragraph numbers in these exact files, so a fresh download could shift them silently.

| edition key | file | Project Gutenberg | sha256 |
|---|---|---|---|
| noli_es | noli_es_rizal_1887.txt | #47584, Noli me tángere, Spanish, Rizal (1887) | a1e437097e5c6b86baa0db08c3d091b76d46f347db5f1e1dd14bdfb1d3f84f8e |
| noli_tl | noli_tl_poblete_1909.txt | #20228, Noli Me Tangere, Tagalog, Pascual H. Poblete (1909) | 43ef048e077f5a4080f6887b36ea26328ae1ce192891a20f28bf58909b06119a |
| noli_en | noli_en_derbyshire_1912.txt | #6737, The Social Cancer, English, Charles Derbyshire (1912) | edaff46d61e92a7eeea5236280d2c9db7a304210379fa2d65148d097ad02b59e |

License: the works are in the public domain. Each file keeps Project Gutenberg's header and license text as downloaded; do not edit them. `tests/unit/test_corpus_files.py` fails if a file changes, and the digests are pinned in `src/rizalai/corpus/ingest.py` (`RAW_SHA256`), which bootstrap checks before ingesting.
