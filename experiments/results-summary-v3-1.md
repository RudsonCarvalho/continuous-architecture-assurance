# Results Summary v3.1

Corpus: 20 pares em `corpus-v3`.
Reviewer model: `claude-sonnet-4-6`.
Judge model: `claude-haiku-4-5`.
R3_narrow categories: `T01, T02, T07, T08`.

## Scores

| Reviewer | Recall | FP | Flagged | Youden |
|---|---:|---:|---:|---:|
| R1_naive | 1.000 | 0.550 | 1.000 | 0.450 |
| R2_contract | 1.000 | 0.100 | 0.950 | 0.900 |
| R3_narrow | 0.300 | 0.050 | 0.425 | 0.250 |
| R4_over_flagger | 1.000 | 1.000 | 1.000 | 0.000 |
| R5_misattribution | 0.000 | 0.000 | 1.000 | 0.000 |

## Pre-registered Checks

- R4 FP >= 0.40: True
- R3_narrow recall <= 0.40: True
- R5_misattribution recall <= 0.40 and flagged >= 0.80: True
- R5 plausible misattribution check: True
- R1 recall < 1.00: False
- R1 non-silent: True
- Corpus validity pass: False
- Corrobora: False
- Falsifica: False
- Verdict: INCONCLUSIVO

## Audit

- Recomputed scores match: True
- Parse errors: 0
- Schema errors: 0
- Judge errors: 0
- Call errors: 0

## Known Limitation

A checagem de validade do corpus falhou para R1_naive. Se R1 tem recall = 1.00, o corpus saturou o eixo de recall; se R1 fica mudo (flagged = 0 ou recall = 0), a rodada tambem nao fornece sinal valido para discriminacao de recall entre revisores reais.
