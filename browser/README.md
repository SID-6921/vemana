# Vemana in the browser

`index.html` and `vemana-complete.js` run Vemana inside a web page with [wllama](https://github.com/ngxson/wllama)
(llama.cpp compiled to WebAssembly): the Q8_0 GGUF downloads once from Hugging Face and is kept by the browser, and
the text never leaves the device. The same engine runs on [udgamlabs.com/models/vemana](https://udgamlabs.com/models/vemana#try).

```bash
python3 browser/serve.py 8799   # serves the folder with the headers multi-threaded WebAssembly needs
# then open http://localhost:8799
```

Several threads need cross-origin isolation (`Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: credentialless`), which `serve.py` sets; without them the page runs on one thread.
