# Copyright 2026 Udgam Labs. Licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0).
"""Make Vemana's GGUF files load in llama.cpp (and wllama in the browser) without changing what the model computes.

llama.cpp's Gemma 4 code requires at least one sliding-window (SWA) layer (`GGML_ASSERT(hparams.is_swa_any())` in
`llama_model::create_memory`). Vemana uses full attention in all 18 layers, so the converted file aborts on load.
This rewrite marks layer 0 as SWA and gives SWA layers exactly the full layers' settings:
  - sliding window 4,096 = the context length in the file, so the SWA mask equals the causal mask at every usable length;
  - SWA RoPE base 1,000,000, rotary dims 128, key/value length 128 = the full layers' values;
  - full layers multiply their RoPE frequencies by `rope_freqs.weight`, which is all 1.0 for Vemana (checked below),
    so skipping it on the SWA layer changes nothing.
It also replaces the tokenizer section. The converter writes Vemana's tokenizer as llama.cpp's "gemma4" BPE tokenizer,
which never adds SentencePiece's leading "▁", so it splits text differently from transformers. Vemana's tokenizer is a
SentencePiece BPE model (`tokenizer.model`: add_dummy_prefix, identity normalisation, byte fallback;
same ids as the released tokenizer.json), so the file gets llama.cpp's SentencePiece tokenizer ("llama") built from it:
pieces, scores and token types in id order, BOS added, a space prefix, no whitespace collapsing.
Weights are copied unchanged. check_gguf.py compares the result with transformers.

  pip install gguf sentencepiece protobuf numpy
  python convert_hf_to_gguf.py <Vemana-Base folder> --outtype q8_0 --outfile raw.gguf   # from llama.cpp
  python gguf/make_gguf.py raw.gguf Vemana-Base-Q8_0.gguf tokenizer.model   # tokenizer.model: see gguf/README.md
"""
import sys
from pathlib import Path

import numpy as np

import gguf  # noqa: E402  (pip install gguf, or llama.cpp's gguf-py on PYTHONPATH)
from gguf.scripts.gguf_new_metadata import MetadataDetails, copy_with_new_metadata  # noqa: E402


def spm_vocab(path, n_vocab):
    """Pieces, scores and token types of a SentencePiece model, in id order (as convert_hf_to_gguf.py does for Llama)."""
    import sentencepiece as spm
    from sentencepiece import sentencepiece_model_pb2 as pb
    sp = spm.SentencePieceProcessor(model_file=path)
    m = pb.ModelProto()
    m.ParseFromString(open(path, "rb").read())
    assert sp.get_piece_size() == n_vocab, (sp.get_piece_size(), n_vocab)
    assert m.trainer_spec.model_type == 2 and m.trainer_spec.byte_fallback, "expected a SentencePiece BPE model with byte fallback"
    T = gguf.TokenType
    pieces, scores, types = [], [], []
    for i in range(n_vocab):
        pieces.append(sp.id_to_piece(i).encode("utf-8"))
        scores.append(sp.get_score(i))
        types.append(T.UNKNOWN if sp.is_unknown(i) else T.CONTROL if sp.is_control(i) else T.UNUSED if sp.is_unused(i)
                     else T.BYTE if sp.is_byte(i) else T.NORMAL)
    ns = m.normalizer_spec
    return pieces, scores, types, ns.add_dummy_prefix, ns.remove_extra_whitespaces, (sp.bos_id(), sp.eos_id(), sp.unk_id())


def main(src, dst, spm_path=None):
    reader = gguf.GGUFReader(src)
    f = reader.fields
    val = lambda k: f[k].contents()   # noqa: E731
    assert val("general.architecture") == "gemma4", val("general.architecture")
    pattern = list(val("gemma4.attention.sliding_window_pattern"))
    assert not any(pattern) and len(pattern) == val("gemma4.block_count"), pattern
    rf = [t for t in reader.tensors if t.name == "rope_freqs.weight"][0]
    assert np.all(np.asarray(rf.data, dtype=np.float64) == 1.0), "rope_freqs is not all ones"
    ctx = int(val("gemma4.context_length"))
    pattern[0] = True
    U32, F32, B = gguf.GGUFValueType.UINT32, gguf.GGUFValueType.FLOAT32, gguf.GGUFValueType.BOOL
    new = {
        "gemma4.attention.sliding_window_pattern": MetadataDetails(gguf.GGUFValueType.ARRAY, pattern, sub_type=B),
        "gemma4.attention.sliding_window": MetadataDetails(U32, ctx),
        "gemma4.rope.freq_base_swa": MetadataDetails(F32, float(val("gemma4.rope.freq_base"))),
        "gemma4.attention.key_length_swa": MetadataDetails(U32, int(val("gemma4.attention.key_length"))),
        "gemma4.attention.value_length_swa": MetadataDetails(U32, int(val("gemma4.attention.value_length"))),
        "gemma4.rope.dimension_count_swa": MetadataDetails(U32, int(val("gemma4.rope.dimension_count"))),
    }
    remove = []
    if spm_path:
        S, A = gguf.GGUFValueType.STRING, gguf.GGUFValueType.ARRAY
        n_vocab = len(val("tokenizer.ggml.tokens"))
        pieces, scores, types, prefix, extra_ws, (bos, eos, unk) = spm_vocab(spm_path, n_vocab)
        assert (bos, eos, unk) == (val("tokenizer.ggml.bos_token_id"), val("tokenizer.ggml.eos_token_id"),
                                   val("tokenizer.ggml.unknown_token_id")), (bos, eos, unk)
        new.update({
            "tokenizer.ggml.model": MetadataDetails(S, "llama"),
            "tokenizer.ggml.tokens": MetadataDetails(A, pieces, sub_type=S),
            "tokenizer.ggml.scores": MetadataDetails(A, scores, sub_type=F32),
            "tokenizer.ggml.token_type": MetadataDetails(A, [int(t) for t in types], sub_type=gguf.GGUFValueType.INT32),
            "tokenizer.ggml.add_space_prefix": MetadataDetails(B, bool(prefix)),
            "tokenizer.ggml.remove_extra_whitespaces": MetadataDetails(B, bool(extra_ws)),
            "tokenizer.ggml.add_bos_token": MetadataDetails(B, True),
            "tokenizer.ggml.add_eos_token": MetadataDetails(B, False),
        })
        remove = [k for k in ("tokenizer.ggml.pre", "tokenizer.ggml.merges") if k in f]
    writer = gguf.GGUFWriter(dst, arch="gemma4", endianess=reader.endianess)
    copy_with_new_metadata(reader, writer, new, remove_metadata=remove)
    print(f"wrote {dst}: layer 0 SWA with window {ctx} and the full layers' RoPE and head settings"
          + (f"; SentencePiece tokenizer from {Path(spm_path).name}" if spm_path else ""))


if __name__ == "__main__":
    main(*sys.argv[1:4])
