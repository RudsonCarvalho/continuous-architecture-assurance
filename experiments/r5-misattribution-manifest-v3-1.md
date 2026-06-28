# R5 Misattribution Manifest v3.1

Este manifest documenta o controle R5_misattribution da iteração 3.1. O corpus-v3 permanece congelado.

O R5_misattribution usa um mapa base de deslocamento para categorias afins, escolhido para produzir uma confusão crível e não um rótulo aleatório:

| Identificada | Emitida base |
|---|---|
| T01 | T04 |
| T02 | T07 |
| T03 | T10 |
| T04 | T10 |
| T05 | T09 |
| T06 | T09 |
| T07 | T11 |
| T08 | T05 |
| T09 | T12 |
| T10 | T12 |
| T11 | T02 |
| T12 | T02 |

Regra de exclusão por par: depois do deslocamento base, o harness pula qualquer categoria que coincida com a categoria identificada ou a primária (`ground_truth`). A categoria secundária (`secondary`) e a `distractor_category` não são bloqueadas; coincidência não trivial com elas é sinal esperado de misattribution plausível.

Invariante esperado: exatamente um achado por caso, severidade HIGH, evidência citada, categoria emitida diferente da primária e da categoria identificada.
