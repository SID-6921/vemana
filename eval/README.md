# Vemana evaluation: fresh Telugu text, bits per byte

The code behind every bits-per-byte number in this repository. It builds a set of new Telugu Wikipedia pages for any
date range, scores any Hugging Face causal language model on it, and compares two models with a paired bootstrap.

| File | What it does |
|---|---|
| `build_te.py` | Builds a fresh Telugu Wikipedia set: `crawl` collects candidate pages, `finalize` re-checks them and writes `data/test.parquet` |
| `score.py` | Bits per byte of a model on a set, with a result per page |
| `compare.py` | Paired bootstrap on two result files: the gap and its 95% interval |
| `make_nopunct.py` | Writes the punctuation-free copy of `te-2026-10` used for one check |

Install:

```bash
pip install torch "transformers>=5.19" pyarrow huggingface_hub
```

Run the commands below from this folder (`eval/`).

## 1. Build a fresh set

A fresh set is new Telugu Wikipedia pages created after the release of every model you want to compare, so none of
them can have seen the text. The builder keeps new mainspace pages only and drops redirects, recreated pages, pages
copied or split from others, lists, disambiguation pages, bot-created pages, duplicates and template-like pages. A page
needs at least 2,500 bytes of wikitext, at least 120 words of prose (long pages are cut at 1,200 words) and at least 85%
Telugu script. `finalize` then re-checks every page for deletion, hidden revisions and suspected AI-generated text.

Any date range (creation dates, inclusive):

```bash
python build_te.py crawl --wiki-start 2026-11-01 --wiki-end 2026-11-30 \
    --cache-dir cache --raw-dir raw/te-2026-11 --out te-2026-11.crawl.jsonl
python build_te.py finalize te-2026-11.crawl.jsonl --out-dir te-2026-11
# -> te-2026-11/data/test.parquet, excluded.jsonl, build_summary.json
```

The three sets in the results, rebuilt with the same settings (the other options at their defaults, including a cap of
6,000,000 bytes per set, which only the summer set reached):

```bash
python build_te.py crawl --wiki-start 2026-09-01 --wiki-end 2026-10-22 --seed 20261023 \
    --cache-dir cache --raw-dir raw/te-2026-10 --out te-2026-10.crawl.jsonl
python build_te.py finalize te-2026-10.crawl.jsonl --out-dir te-2026-10

python build_te.py crawl --wiki-start 2026-10-23 --wiki-end 2026-10-26 --seed 20261027 \
    --cache-dir cache --raw-dir raw/te-2026-10b --out te-2026-10b.crawl.jsonl
python build_te.py finalize te-2026-10b.crawl.jsonl --out-dir te-2026-10b

python build_te.py crawl --wiki-start 2026-07-01 --wiki-end 2026-08-31 --seed 20261027 \
    --cache-dir cache --raw-dir raw/te-2026-summer --out te-2026-summer.crawl.jsonl
python build_te.py finalize te-2026-summer.crawl.jsonl --out-dir te-2026-summer
```

- We built `te-2026-10` on 23 October 2026 (416 pages) and the other two on 27 October 2026 (29 and 477 pages), all
  with this exact `build_te.py`. Pages are fetched at their current revision, so a set rebuilt later can differ a
  little from ours: pages edited, deleted or tagged since then.
- `--cache-dir` stores every raw response, so a second run of the same command gives the same set.
- The builder waits 1.2 seconds between Wikipedia API calls, so a long date range takes a while.
- Before you run it, change `UA` near the top of `build_te.py` to name your own project and a way to contact you, as
  Wikimedia's User-Agent policy asks.
- `python build_te.py selftest` runs the text filters' offline checks.
- The built sets are Telugu Wikipedia text under CC BY-SA 4.0. Each row carries its page's URL, revision and
  attribution; keep them if you share a set.

## 2. Score a model

```bash
python score.py udgamlabs/Vemana-Base --data te-2026-10/data/test.parquet --ctx 1024 --out runs/vemana.json
python score.py SOME/MODEL --data te-2026-10/data/test.parquet --ctx 1024 --out runs/some-model.json
```

- Bits per byte = the total bits for every token of every page divided by the pages' total UTF-8 bytes. Lower is
  better. Each page is scored on its own, from the model's BOS token when its tokenizer defines one (`--add-bos auto`),
  with a window that slides by half its length, so every token is scored exactly once.
- Always pass `--data` (the default points at another of our sets) and `--ctx` (the default is 2,048). We used
  1,024 for every model, the length Vemana was trained at, and 512 for Goldfish, its limit.
- `--dtype float32` is the default and what we used. Our release run also allowed TF32 matrix multiplies on the GPU
  (`torch.backends.cuda.matmul.allow_tf32 = True`); `score.py` on its own runs full float32. Expect small differences
  across hardware: Vemana's per-page bits in the release run matched an earlier run of the same script on another GPU
  to within 6.7e-5 (relative).
- `--revision` pins a model commit, and the result file records the commit that was scored. Models with their own
  modelling code need `--trust-remote-code`; read that code first.
- The result file has the headline `bpb` and one row per page (`bits`, `bytes`, `tokens`).

## 3. Compare two models

```bash
python compare.py runs/some-model.json runs/vemana.json
# fresh-text: udgamlabs/Vemana-Base - SOME/MODEL = ... bpb  [95% CI ..., ...]  (n=416)  *
```

`compare.py` prints B minus A for each pair of files (here Vemana minus the other model, so negative means Vemana is
better), from 4,000 resamples of the shared pages with seed 0. A `*` marks an interval that excludes zero. On our
release-run files it gives −0.0224 [−0.0240, −0.0210] for Vemana minus nanochat-telugu-560M on `te-2026-10`, the same as
the release-gate table.

## 4. The punctuation-free check

```bash
python make_nopunct.py      # reads te-2026-10/data/test.parquet, writes te-2026-10/data/test_nopunct.parquet
python score.py udgamlabs/Vemana-Base --data te-2026-10/data/test_nopunct.parquet --ctx 1024 --out runs/vemana-nopunct.json
```

It removes ASCII punctuation and collapses every run of whitespace, line breaks included, into one space. It is a
diagnostic, not the headline test.

## Not covered here

The covered-text numbers for Pothana (bits on the bytes its tokenizer does not map to an unknown token), the
Dhee-normalised copy of the set, the multiple-choice tests (lm-eval) and the release-gate analysis were produced by our
release job, which is not in this repository. Their results are in
[../results/release-gate-2026-10-27.md](../results/release-gate-2026-10-27.md).
