# Resultado do Experimento de Calibração

**Veredito: H1 FALSIFICADA**, pelo critério explícito da seção 4 do protocolo ("ou se os controles degenerados passam") — o controle degenerado R3 (over-approver) não foi capturado pela métrica pareada: obteve recall=0,93 e o melhor índice de Youden das quatro condições (0,87), quando o protocolo previa que ele deveria ser reprovado por recall baixo (≤0,40).

Execução real completa: 4 revisores × 30 casos = 120 chamadas ao modelo, 0 erros de parsing/schema/chamada. Números abaixo vêm diretamente de `results/scores.json` e foram reconferidos por reconstrução independente a partir de `results/raw_results.json` (caso a caso, ver seção 4).

## 1. Números finais

| Revisor | Recall | FP rate | Youden (recall − FP) |
|---|---|---|---|
| R1_naive | 1,00 | 0,60 | 0,40 |
| R2_contract | 1,00 | 0,33 | 0,67 |
| R3_over_approver | 0,93 | 0,07 | 0,87 |
| R4_over_flagger | 1,00 | 1,00 | 0,00 |

Saída literal do script (`calib_experiment.py`):

```
R1_naive: recall=1.00 fp=0.60 youden=0.40
R2_contract: recall=1.00 fp=0.33 youden=0.67
R3_over_approver: recall=0.93 fp=0.07 youden=0.87
R4_over_flagger: recall=1.00 fp=1.00 youden=0.00
Critérios: C1(contrato>naive)=False  C2(pega over-flagger)=True  C3(pega over-approver)=False
H1 NÃO corroborada — ver protocolo, seção 4
```

## 2. Aplicação dos critérios da seção 4 (verbatim, fixados antes da execução)

> O experimento **corrobora H1** se, simultaneamente:
> 1. Recall(R2) ≥ Recall(R1) + 0,15 com FP(R2) ≤ FP(R1); e
> 2. R4 apresenta FP ≥ 0,40 (o eval pega o over-flagger); e
> 3. R3 apresenta Recall ≤ 0,40 (o eval pega o over-approver).
>
> O experimento **falsifica H1** se R1 ≈ R2 (diferença < 0,10 em Youden) — o contrato não acrescenta nada mensurável — ou se os controles degenerados passam. Resultado intermediário: ajustar contrato/taxonomia e rodar segunda iteração antes de concluir.

**Perna "corrobora" (calculada pelo script, `preregistered_criteria()`):**

- C1 — Recall(R2)=1,00 ≥ Recall(R1)=1,00 + 0,15 = 1,15? **Não.** Ambos já estão no teto de recall; a cláusula é estruturalmente impossível de satisfazer quando a linha de base já é 1,00 (ver seção 5).
- C2 — FP(R4)=1,00 ≥ 0,40? **Sim.** O over-flagger é capturado.
- C3 — Recall(R3)=0,93 ≤ 0,40? **Não**, por uma margem grande (0,93 vs. 0,40). O over-approver não é capturado.

C1 ∧ C2 ∧ C3 = Falso → **H1 não corrobora** (idêntico ao que o script imprime).

**Perna "falsifica" (não codificada no script — o protocolo atribui esse julgamento ao humano, seção 5: "Decisão pelos critérios da seção 4"; aplicada aqui sobre os números reais, sem ajuste):**

- R1 ≈ R2 (diferença de Youden < 0,10)? Youden(R1)=0,40, Youden(R2)=0,67 → diferença = 0,27. **Não se aplica** — o contrato tem efeito mensurável, concentrado quase inteiramente na redução de falsos positivos (seção 4 abaixo), não na recall (que já estava saturada).
- Os controles degenerados passam? R4 não passa — é corretamente capturado pelo FP (1,00) e tem o pior Youden das quatro condições, exatamente como desenhado. **R3 passa**: foi construído para ser um aprovador frouxo e deveria ser reprovado por recall ≤ 0,40; em vez disso obteve recall=0,93 e o **melhor** Youden de todas as condições. Um controle degenerado passou.

Como pelo menos uma das duas cláusulas de falsificação se confirma, **H1 é falsificada** — não apenas "não corroborada". A distinção importa: "não corroborada" é compatível com resultado intermediário; "falsificada" é uma classificação mais específica e mais forte, e é a que os critérios pré-registrados produzem aqui.

## 3. Por que R3 passou (evidência caso a caso)

R3 (over-approver) foi instruído a aprovar a menos que o problema seja óbvio e catastrófico. Na prática, contra este corpus e este modelo, ele:

- Recall 14/15: identificou corretamente a categoria de causa em todos os `case_fail`, exceto **P03** (cache stampede de metadados de vídeo, T03) — o único falso negativo de R3 no corpus inteiro.
- FP 1/15: levantou alarme falso em apenas um `case_healthy` — **P06**, e mesmo esse caso é a categoria **secundária** do par (T12), não a primária (T05).

Ou seja: a persona "seja permissivo" não suprimiu o julgamento de engenharia do modelo de forma mensurável neste corpus. Isso contradiz a expectativa de desenho do protocolo (seção 2: "o eval precisa reprová-lo por recall baixo") e é, em si, um achado relevante — não um defeito do experimento.

## 4. Por que o contrato (R2) reduz FP sem mudar recall

Recall(R1) = Recall(R2) = 1,00: ambos capturam todos os 15 `case_fail`. A diferença está inteiramente no FP, reconstruída a partir de `raw_results.json`:

- R1: 9/15 falsos positivos. Dos quais 6 são alarmes na **própria categoria primária** do par (P02, P03, P04, P07, P08, P15) — o revisor não confiou na mitigação explícita já descrita no `case_healthy`. Os outros 3 (P01, P06, P11) batem na categoria **secundária** do par.
- R2: 5/15 falsos positivos. Os alarmes em categoria primária caem de 6 para 2 (restam P02, P04). Os 3 alarmes em categoria secundária (P01, P06, P11) persistem inalterados.

O contrato (exigir citação literal de evidência por categoria) elimina a maior parte do ruído em categoria primária, mas não elimina os alarmes ligados às categorias secundárias dos 4 pares que têm `secondary` definido (P01/T07, P06/T12, P09/T05, P11/T12) — nesses pares, o gêmeo saudável resolve a causa primária mas ainda contém o mecanismo arquitetural da categoria secundária, e um revisor que o cita não está, estritamente, errado. Isso é uma característica estrutural do corpus, não ruído do revisor — ver seção 5.

## 5. R4 (over-flagger): a ilustração desenhada funcionou

R4 tem recall=1,00 (igual a R1 e R2) e FP=1,00 — alarme em 100% dos `case_fail` *e* 100% dos `case_healthy`, sempre na categoria certa. Se a calibração usasse recall isoladamente, R4 empataria com os melhores revisores. Apenas o par recall/FP expõe que ele não discrimina nada. Esta parte do desenho — a razão de existir dois controles degenerados — funcionou exatamente como previsto (critério C2 = verdadeiro).

## 6. Integridade dos dados

- `results/raw_results.json`: 120 registros (4 revisores × 30 casos), reconferidos via grep — 0 ocorrências de `parse_error`, `call_error` ou `schema_errors` não vazio.
- `results/run-log.jsonl`: 120 linhas, 0 marcas de erro.
- Os números de `scores.json` foram recalculados manualmente a partir de `raw_results.json` (contagem de `judge.match` por revisor/variante) e coincidem exatamente com os valores reportados pelo script.
- Um bug real foi encontrado e corrigido durante a execução: `max_tokens=2000` truncava as respostas verbosas de R4, causando `"unterminated JSON object"`. Corrigido para `8192`, e o cache de respostas (que não invalidava por `max_tokens`) passou a validar o JSON antes de reaproveitar uma entrada, tratando respostas truncadas como cache miss. Nenhum prompt, taxonomia ou critério de decisão foi alterado para chegar a essa correção.

## 7. Limitações e notas para uma segunda iteração

Estas notas são posteriores ao veredito e não o alteram — são lidas como diagnóstico para uma eventual segunda iteração, não como atenuante do resultado:

- **Teto de recall no corpus.** R1, R2 e R4 atingiram recall=1,00 e R3 ficou em 0,93 — a cláusula C1 (recall(R2) ≥ recall(R1) + 0,15) é estruturalmente impossível de satisfazer quando a linha de base já está no teto. Toda a discriminação observada neste experimento veio do eixo de FP, não do eixo de recall. Os `case_fail` deste corpus podem estar redigidos de forma muito inequívoca para estressar recall.
- **Persona sozinha não basta para induzir um controle degenerado de baixo recall.** R3 mostra que instruir o modelo a "ser permissivo" não foi suficiente, com este modelo, para suprimir o reconhecimento de uma causa real já descrita no texto. Uma segunda iteração talvez precise de um corpus com sinais de falha mais ambíguos, ou de uma definição de "over-approver" que não dependa só de instrução de persona.
- **Categorias secundárias como fonte estrutural de FP.** Os 4 pares com `secondary` definido (P01, P06, P09, P11) concentram a maior parte dos falsos positivos residuais de R2 e o único FP de R3. Vale reavaliar, numa revisão futura do protocolo, se achados em categoria secundária deveriam contar no denominador de FP — sem alterar retroativamente o corpus ou os resultados já obtidos aqui.
- **Limitações já nomeadas no protocolo permanecem válidas:** corpus de autor único, n=15 pares, um único modelo (Claude) avaliando a si mesmo como juiz.

## 8. Status final

| Item | Status |
|---|---|
| Corpus (15 pares blindados) | Concluído |
| Harness (`calib_experiment.py`) | Validado via dry-run e via execução real (120/120 chamadas, 0 erros) |
| Execução real (4 revisores × 30 casos) | Concluída |
| Veredito sobre H1 | **Falsificada** — controle degenerado R3 não foi capturado pela métrica pareada (seção 2 e 3) |
