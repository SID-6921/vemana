# Vemana release gate: results (run release-1)

Bits per byte, lower is better. Gap = Vemana minus the model on the same pages; negative = Vemana better. 95% intervals from 4,000 page resamples (seed 0). [MEASURED]

**Control** (te-2026-10 re-scored in this run against each model's earlier per-page result):

- Goldfish Telugu 1000mb: OK (416 pages, tokens identical: True, largest relative bits difference 0.0e+00; earlier: Gate 0 part 2 gate0-2 (23 Oct))
- Vemana (ours): OK (416 pages, tokens identical: True, largest relative bits difference 6.7e-05; earlier: main run main-1, final-step-022888/fresh.json (official score.py, H100, 26 Oct))
- Gemma-3-1B: OK (416 pages, tokens identical: True, largest relative bits difference 0.0e+00; earlier: Gate 0 part 3 gate0-3 (23 Oct))
- nanochat-telugu-560M: OK (416 pages, tokens identical: True, largest relative bits difference 0.0e+00; earlier: Step 0 rivals-1 (A40, 25 Oct))
- Pothana Base v2: OK (416 pages, tokens identical: True, largest relative bits difference 0.0e+00; earlier: Step 0 rivals-1 (A40, 25 Oct))
- Sarvam-1: OK (416 pages, tokens identical: True, largest relative bits difference 0.0e+00; earlier: Gate 0 part 3 gate0-3 (23 Oct))

## te-2026-10 (416 pages created 1 Sep-22 Oct 2026)
416 pages, 4,476,833 bytes, 47 editors (top editor 150 pages).

| Model | Params | Bits per byte [95% CI] | Vemana minus model [95% CI] | Covered text (Pothana) | Without top editor: gap |
|---|---|---|---|---|---|
| Sarvam-1 | 2.5B | 0.356 [0.351, 0.361] | +0.005 [-0.001, +0.010] | - | +0.012 [+0.004, +0.019] |
| Vemana (ours) | 278.2M | 0.361 [0.353, 0.367] | - | - | 0.373 |
| nanochat-telugu-560M | 561M | 0.383 [0.376, 0.390] | -0.022 [-0.024, -0.021] | - | -0.023 [-0.026, -0.021] |
| Dhee-Pravega-OG Atom | 645.6M | 0.393 [0.385, 0.400] | -0.032 [-0.034, -0.031] | - | -0.035 [-0.037, -0.033] |
| Pothana Base v2 | 222M unique (370M unrolled) | 0.440 [0.433, 0.448] | -0.080 [-0.081, -0.078] | 0.426 (3.6% hidden); gap -0.066 [-0.067, -0.064] | -0.083 [-0.085, -0.081] |
| Pothana stage-a-plus | 230M unique | 0.450 [0.443, 0.458] | -0.090 [-0.092, -0.088] | 0.436 (Step 0) | -0.093 [-0.095, -0.091] |
| Goldfish Telugu 1000mb | 125M | 0.458 [0.450, 0.465] | -0.097 [-0.099, -0.095] | - | -0.096 [-0.100, -0.093] |
| Pothana sp-base-300M | 387M unique | 0.462 [0.455, 0.469] | -0.102 [-0.105, -0.099] | - | -0.106 [-0.111, -0.101] |
| Gemma-3-1B | 1.0B | 0.484 [0.474, 0.493] | -0.123 [-0.127, -0.119] | - | -0.126 [-0.131, -0.121] |
| Qwen3.5-0.8B-Base | 0.87B | 0.584 [0.577, 0.591] | -0.223 [-0.228, -0.219] | - | -0.220 [-0.227, -0.215] |
| Gemma-3-270m | 268M | 0.585 [0.575, 0.594] | -0.224 [-0.228, -0.220] | - | -0.229 [-0.235, -0.224] |
| Qwen3-0.6B-Base | 0.6B | 0.692 [0.685, 0.699] | -0.332 [-0.336, -0.327] | - | -0.328 [-0.334, -0.322] |
| gpt-2-telugu1 | 98M | 0.786 [0.774, 0.797] | -0.425 [-0.436, -0.414] | - | -0.402 [-0.416, -0.389] |
| LFM2.5-230M-Base | 230M | 1.709 [1.701, 1.716] | -1.348 [-1.355, -1.341] | - | -1.335 [-1.342, -1.327] |

## te-2026-10b (pages created 23-26 Oct 2026; the newer set fixed in advance)
29 pages, 285,496 bytes, 9 editors (top editor 16 pages).

| Model | Params | Bits per byte [95% CI] | Vemana minus model [95% CI] | Covered text (Pothana) | Without top editor: gap |
|---|---|---|---|---|---|
| Sarvam-1 | 2.5B | 0.337 [0.313, 0.359] | +0.009 [-0.009, +0.022] | - | - |
| Vemana (ours) | 278.2M | 0.346 [0.311, 0.372] | - | - | - |
| nanochat-telugu-560M | 561M | 0.364 [0.330, 0.388] | -0.018 [-0.021, -0.015] | - | - |
| Dhee-Pravega-OG Atom | 645.6M | 0.371 [0.336, 0.397] | -0.025 [-0.030, -0.022] | - | - |
| Pothana Base v2 | 222M unique (370M unrolled) | 0.425 [0.387, 0.454] | -0.079 [-0.088, -0.069] | 0.410 (4.1% hidden); gap -0.065 [-0.074, -0.055] | - |
| Goldfish Telugu 1000mb | 125M | 0.435 [0.400, 0.464] | -0.090 [-0.097, -0.083] | - | - |
| Gemma-3-1B | 1.0B | 0.441 [0.395, 0.477] | -0.095 [-0.108, -0.080] | - | - |

## te-2026-summer (pages created 1 Jul-31 Aug 2026; supplementary)
477 pages, 6,001,285 bytes, 33 editors (top editor 210 pages).

| Model | Params | Bits per byte [95% CI] | Vemana minus model [95% CI] | Covered text (Pothana) | Without top editor: gap |
|---|---|---|---|---|---|
| Sarvam-1 | 2.5B | 0.365 [0.360, 0.370] | +0.020 [+0.017, +0.024] | - | - |
| Vemana (ours) | 278.2M | 0.385 [0.379, 0.392] | - | - | - |
| nanochat-telugu-560M | 561M | 0.408 [0.402, 0.414] | -0.023 [-0.024, -0.022] | - | - |
| Dhee-Pravega-OG Atom | 645.6M | 0.414 [0.408, 0.420] | -0.029 [-0.030, -0.028] | - | - |
| Pothana Base v2 | 222M unique (370M unrolled) | 0.456 [0.451, 0.462] | -0.071 [-0.073, -0.069] | 0.444 (3.9% hidden); gap -0.058 [-0.060, -0.057] | - |
| Goldfish Telugu 1000mb | 125M | 0.480 [0.474, 0.486] | -0.095 [-0.096, -0.093] | - | - |
| Gemma-3-1B | 1.0B | 0.502 [0.495, 0.509] | -0.117 [-0.120, -0.113] | - | - |

## Diagnostics on te-2026-10

- **fresh_ctx512**: Vemana 0.366; nanochat-telugu-560M (fresh) 0.383, gap -0.017 [-0.019, -0.016]; Dhee-Pravega-OG Atom (fresh) 0.393, gap -0.027 [-0.029, -0.026]; Pothana Base v2 (fresh) 0.440, gap -0.075 [-0.076, -0.073]; Pothana stage-a-plus (fresh) 0.450, gap -0.085 [-0.087, -0.083]; Goldfish Telugu 1000mb (fresh) 0.458, gap -0.092 [-0.094, -0.090]; Pothana sp-base-300M (fresh) 0.462, gap -0.096 [-0.100, -0.093]; Gemma-3-1B (fresh) 0.484, gap -0.118 [-0.121, -0.114]; Qwen3.5-0.8B-Base (fresh) 0.584, gap -0.218 [-0.223, -0.214]; Gemma-3-270m (fresh) 0.585, gap -0.219 [-0.223, -0.215]; Qwen3-0.6B-Base (fresh) 0.692, gap -0.326 [-0.331, -0.322]; gpt-2-telugu1 (fresh) 0.786, gap -0.420 [-0.430, -0.410]; LFM2.5-230M-Base (fresh) 1.709, gap -1.343 [-1.350, -1.336]; Sarvam-1 (fresh) 0.356, gap +0.010 [+0.004, +0.015]
- **fresh_nopunct**: Vemana 0.373; nanochat-telugu-560M (fresh_nopunct) 0.381, gap -0.008 [-0.009, -0.007]; Dhee-Pravega-OG Atom (fresh_nopunct) 0.402, gap -0.030 [-0.031, -0.028]; Pothana Base v2 (fresh_nopunct) 0.452, gap -0.079 [-0.080, -0.077]; Pothana stage-a-plus (fresh_nopunct) 0.463, gap -0.090 [-0.092, -0.089]; Goldfish Telugu 1000mb (fresh_nopunct) 0.474, gap -0.102 [-0.104, -0.099]; Pothana sp-base-300M (fresh_nopunct) 0.401, gap -0.028 [-0.029, -0.027]; Gemma-3-1B (fresh_nopunct) 0.532, gap -0.159 [-0.164, -0.154]; Qwen3.5-0.8B-Base (fresh_nopunct) 0.593, gap -0.220 [-0.225, -0.216]; Gemma-3-270m (fresh_nopunct) 0.615, gap -0.242 [-0.248, -0.237]; Qwen3-0.6B-Base (fresh_nopunct) 0.695, gap -0.322 [-0.327, -0.318]; gpt-2-telugu1 (fresh_nopunct) 0.763, gap -0.390 [-0.399, -0.381]; LFM2.5-230M-Base (fresh_nopunct) 1.706, gap -1.333 [-1.340, -1.326]; Sarvam-1 (fresh_nopunct) 0.373, gap -0.000 [-0.006, +0.005]
- **fresh_dheenorm**: Vemana 0.360; Dhee-Pravega-OG Atom (fresh) 0.394, gap -0.034 [-0.036, -0.033]

## Rule A_under_300M
- Rule: Vemana <= 0.406 and paired 95% interval of (Vemana - Pothana v2, its better score) below zero
- Pass: **True**
- {"vemana_bpb": 0.3606365540970816, "pothana_v2_score": 0.4263617122167728, "gap": {"gap": -0.06572515811969121, "ci95": [-0.06735618815338978, -0.06406548003005536], "n": 416, "share_resamples_vemana_better": 1.0}, "pass": true}

## Rule B_under_1B
- Rule: B - Vemana >= 0.02 with the interval below zero; below zero also at window 512, without the top editor, and on te-2026-10b
- Pass: **True**
- {"B": 0.38308224578885963, "B_model": "nanochat-telugu-560M", "vemana_bpb": 0.3606365540970816, "margin": 0.022445691691778014, "gap": {"gap": -0.022445691691778014, "ci95": [-0.023910957869995864, -0.02103575704563626], "n": 416, "share_resamples_vemana_better": 1.0}, "robustness": {"ctx512": {"gap": -0.017251161216657485, "ci95": [-0.018577436880613585, -0.015929300940237756], "n": 416, "share_resamples_vemana_better": 1.0, "rival_bpb": 0.38308224578885963, "rival_run": "fresh"}, "without_top_editor": {"gap": -0.023481176547705984, "ci95": [-0.025837823861237064, -0.021359614621572265], "n": 266, "share_resamples_vemana_better": 1.0}, "newer_set_fresh_b": {"gap": -0.017857188794252243, "ci95": [-0.021390846320411938, -0.014729092399450139], "n": 29, "share_resamples_vemana_better": 1.0}}, "robustness_pass": {"ctx512": true, "without_top_editor": true, "newer_set_fresh_b": true}, "supplementary_summer": {"gap": -0.0227195531406153, "ci95": [-0.023736136774599292, -0.021741880856101847], "n": 477, "share_resamples_vemana_better": 1.0}, "pass_main": true, "pass_all": true}

## lm-eval (0-shot, BOS first; accuracy %, 95% item bootstrap; gap = Vemana minus model, points)

| Task (chance) | Vemana (ours) | nanochat-telugu-560M | Dhee-Pravega-OG Atom | Goldfish Telugu 1000mb | Gemma-3-1B | Qwen3.5-0.8B-Base | Gemma-3-270m | Qwen3-0.6B-Base | gpt-2-telugu1 | LFM2.5-230M-Base | Sarvam-1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| belebele_te_letter (25%) | 25.1 [22.3, 28.0] | 23.0 [20.2, 25.8]; gap +2.1 [-1.0, +5.3] | 22.4 [19.8, 25.1]; gap +2.7 [-0.6, +5.9] | 22.7 [19.9, 25.6]; gap +2.4 [-0.9, +5.9] | 24.9 [22.1, 27.8]; gap +0.2 [-3.6, +4.1] | 35.6 [32.6, 38.7]; gap -10.4 [-14.4, -6.3] | 23.3 [20.6, 26.1]; gap +1.8 [-1.9, +5.7] | 30.4 [27.6, 33.6]; gap -5.3 [-9.4, -1.1] | 24.6 [21.8, 27.3]; gap +0.6 [-2.8, +3.9] | 24.7 [21.9, 27.4]; gap +0.4 [-3.7, +4.8] | 54.0 [50.8, 57.3]; gap -28.9 [-33.1, -24.7] |
| belebele_te_cloze (25%) | 26.1 [23.3, 29.0] | 26.8 [23.9, 29.6]; gap -0.7 [-3.1, +1.8] | 27.0 [24.2, 30.0]; gap -0.9 [-3.3, +1.4] | 24.2 [21.4, 27.0]; gap +1.9 [-1.0, +4.7] | 25.9 [23.0, 28.8]; gap +0.2 [-2.6, +2.9] | 26.8 [23.9, 29.7]; gap -0.7 [-3.7, +2.3] | 25.2 [22.4, 28.0]; gap +0.9 [-2.0, +3.8] | 29.7 [26.7, 32.7]; gap -3.6 [-6.4, -0.7] | 23.7 [21.0, 26.4]; gap +2.4 [-0.6, +5.4] | 27.0 [24.1, 29.8]; gap -0.9 [-4.1, +2.3] | 37.6 [34.3, 40.7]; gap -11.4 [-14.7, -8.2] |
| milu_te_letter (25%) | 25.3 [24.3, 26.3] | 25.3 [24.3, 26.3]; gap +0.0 [-0.8, +0.9] | 24.8 [23.8, 25.8]; gap +0.5 [-0.2, +1.2] | 25.2 [24.2, 26.2]; gap +0.1 [-0.7, +0.8] | 25.0 [24.0, 26.0]; gap +0.3 [-1.0, +1.7] | 31.1 [30.1, 32.2]; gap -5.8 [-7.3, -4.4] | 24.1 [23.2, 25.1]; gap +1.2 [-0.4, +2.7] | 29.2 [28.1, 30.2]; gap -3.9 [-5.2, -2.5] | 25.0 [24.0, 26.0]; gap +0.3 [-0.7, +1.2] | 25.5 [24.5, 26.5]; gap -0.2 [-1.7, +1.3] | 40.1 [39.0, 41.3]; gap -14.9 [-16.5, -13.4] |
| milu_te_cloze (25%) | 30.2 [29.2, 31.3] | 29.3 [28.2, 30.3]; gap +0.9 [+0.0, +1.7] | 27.2 [26.2, 28.2]; gap +3.0 [+2.0, +3.9] | 27.0 [26.0, 28.1]; gap +3.2 [+2.1, +4.2] | 27.1 [26.1, 28.1]; gap +3.1 [+1.9, +4.1] | 26.3 [25.3, 27.3]; gap +3.9 [+2.7, +5.0] | 25.3 [24.3, 26.3]; gap +4.9 [+3.7, +6.0] | 26.7 [25.7, 27.7]; gap +3.5 [+2.3, +4.7] | 24.9 [23.9, 25.9]; gap +5.3 [+4.2, +6.4] | 25.2 [24.2, 26.2]; gap +5.0 [+3.7, +6.2] | 36.9 [35.8, 38.0]; gap -6.7 [-7.9, -5.6] |
| indicxnli_te (33%) | 35.0 [33.7, 36.3] | 34.9 [33.6, 36.2]; gap +0.1 [-0.7, +0.9] | 36.7 [35.4, 38.1]; gap -1.7 [-2.8, -0.6] | 32.9 [31.6, 34.2]; gap +2.1 [+1.2, +3.0] | 35.5 [34.2, 36.9]; gap -0.5 [-1.5, +0.4] | 34.9 [33.5, 36.2]; gap +0.2 [-1.3, +1.5] | 34.1 [32.7, 35.4]; gap +1.0 [-0.9, +2.7] | 35.8 [34.5, 37.1]; gap -0.8 [-3.0, +1.5] | 35.6 [34.3, 36.9]; gap -0.6 [-1.6, +0.5] | 33.5 [32.1, 34.8]; gap +1.5 [-0.7, +3.7] | 46.7 [45.3, 48.1]; gap -11.7 [-13.0, -10.5] |
| indiccopa_te (50%) | 58.4 [54.2, 62.8] | 60.4 [56.2, 64.6]; gap -2.0 [-5.2, +1.2] | 59.0 [54.6, 63.2]; gap -0.6 [-4.0, +2.8] | 56.6 [52.0, 61.0]; gap +1.8 [-1.8, +5.2] | 57.4 [53.0, 62.0]; gap +1.0 [-2.8, +4.8] | 55.6 [51.4, 60.0]; gap +2.8 [-1.8, +7.4] | 56.8 [52.6, 61.2]; gap +1.6 [-2.8, +5.8] | 53.4 [49.0, 57.6]; gap +5.0 [+0.4, +9.6] | 55.4 [51.0, 59.8]; gap +3.0 [-0.8, +6.8] | 51.4 [47.0, 55.6]; gap +7.0 [+2.0, +11.8] | 63.6 [59.4, 67.6]; gap -5.2 [-8.6, -1.8] |
