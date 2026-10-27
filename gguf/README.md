# GGUF files for llama.cpp and the browser

The files are on Hugging Face: [udgamlabs/Vemana-Base-GGUF](https://huggingface.co/udgamlabs/Vemana-Base-GGUF)
(`Vemana-Base-Q8_0.gguf`, 297 MB; `Vemana-Base-F16.gguf`, 558 MB). This folder rebuilds and checks them.

- `make_gguf.py`: llama.cpp's Gemma 4 code needs at least one sliding-window layer, and Vemana uses full attention in
  every layer, so a plain conversion aborts on load. The script marks layer 0 as sliding with a window of 4,096 tokens
  (the file's whole context) and the same rotary and head settings as the other layers, so the computation is unchanged,
  and stores the tokenizer as Vemana's SentencePiece model (`tokenizer.model`, same ids as the released
  `tokenizer.json`) so llama.cpp splits text exactly like transformers. Weights are copied unchanged.
- `check_gguf.py`: compares a GGUF file with the transformers model: tokenization on fresh pages, greedy continuations,
  and perplexity computed the way `llama-perplexity` does.
- `check_results_2026-10-27.json`: our run of that check: tokenization identical on 40 of 40 pages; perplexity 15.764
  (transformers, float32), 15.764 (F16), 15.765 (Q8_0); greedy continuations identical on 4 of 4 prompts (F16) and 3 of
  4 (Q8_0).

```bash
pip install gguf sentencepiece protobuf numpy
python llama.cpp/convert_hf_to_gguf.py <local copy of udgamlabs/Vemana-Base> --outtype q8_0 --outfile raw-Q8_0.gguf
python gguf/make_gguf.py raw-Q8_0.gguf Vemana-Base-Q8_0.gguf gguf/tokenizer.model
```
