// Vemana in the browser: llama.cpp compiled to WebAssembly (wllama), the Q8_0 GGUF, plain text completion.
// Everything runs on the visitor's device; no text is sent anywhere. Used by index.html and the udgamlabs.com page.
import { Wllama } from "https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/esm/index.js";

export const WLLAMA_WASM = "https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/esm/wasm/wllama.wasm";
export const MODEL_URL = "https://huggingface.co/udgamlabs/Vemana-Base-GGUF/resolve/main/Vemana-Base-Q8_0.gguf";
export const SAMPLING = { temperature: 0.8, top_p: 0.95 };   // the model card's quick-start settings
export const LIMITS = { nCtx: 1024, maxNew: 160, maxPromptChars: 1500 };   // trained at 1,024 tokens

export class VemanaComplete {
  constructor() { this.w = null; this.abort = null; }

  async load(modelUrl = MODEL_URL, onProgress = () => {}) {
    this.w = new Wllama({ default: WLLAMA_WASM });
    await this.w.loadModelFromUrl(modelUrl, {
      n_ctx: LIMITS.nCtx,
      useCache: true,
      progressCallback: ({ loaded, total }) => onProgress(loaded, total),
    });
    return { multithread: this.w.isMultithread() };
  }

  // Continue `prompt` (wllama adds <s> itself, as the model was trained). onUpdate(text) while streaming.
  async complete(prompt, onUpdate, { maxNew = LIMITS.maxNew, sampling = SAMPLING } = {}) {
    prompt = String(prompt).slice(0, LIMITS.maxPromptChars);
    this.abort = new AbortController();
    let text = "", ntok = 0, timings = null;
    const t0 = performance.now();
    const stream = await this.w.createCompletion({
      prompt, stream: true, max_tokens: maxNew, stop: ["</s>"], abortSignal: this.abort.signal, ...sampling,
    });
    try {
      for await (const chunk of stream) {
        if (chunk.timings) timings = chunk.timings;
        const piece = chunk.choices?.[0]?.text ?? "";
        if (piece) { text += piece; ntok += 1; onUpdate(text, true); }
      }
    } catch (e) {
      if (e?.name !== "AbortError") throw e;
    }
    const secs = (performance.now() - t0) / 1000;
    onUpdate(text, false);
    const tps = timings?.predicted_per_second ?? ntok / Math.max(secs, 1e-3);
    return { text, tokensPerSecond: tps, chunks: ntok, seconds: secs };
  }

  stop() { this.abort?.abort(); }

  // Self-test: the WASM tokenizer's prompt-token counts must equal transformers' (cases: [{text, ids}]), and greedy
  // decoding must give transformers' greedy continuation (cases with `greedy`).
  async selfTest(cases) {
    const out = [];
    for (const c of cases) {
      const r = await this.w.createCompletion({ prompt: c.text, max_tokens: c.greedy ? c.greedyTokens : 1, temperature: 0 });
      const got = r.choices?.[0]?.text ?? "";
      out.push({ text: c.text, promptTokens: r.usage?.prompt_tokens, expected: c.ids.length,
                 greedyMatch: c.greedy ? got.replace(/^ /, "").startsWith(c.greedy.slice(0, 60)) : null, greedy: got.slice(0, 80) });
    }
    return out;
  }
}
