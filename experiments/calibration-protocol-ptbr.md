# Experimento Mínimo de Falsificação — Calibração de Revisores

**Hipótese central (H1):** o par de métricas *recall de riscos conhecidos* + *taxa de falso positivo*, medido contra um corpus de incidentes reais, discrimina revisores de IA bons de ruins — e, portanto, pode servir de regime de calibração para qualquer "régua" arquitetural.

**Hipótese nula (H0):** as métricas não discriminam — revisores com prompts radicalmente diferentes produzem scores indistinguíveis, ou o revisor degenerado "reprova tudo" passa no eval. Se H0 se sustentar, o claim central do framework cai.

---

## 1. Corpus (o trabalho real está aqui)

**Fonte: postmortems públicos** — reproduzível, publicável, sem dado proprietário. Boas fontes: a coleção `danluu/post-mortems` no GitHub, Kubernetes Failure Stories (k8s.af), e incident reports públicos de Cloudflare, GitHub, GitLab e AWS.

**Tamanho piloto:** 15 pares (30 casos). Suficiente para sinal direcional; não para significância forte — e tudo bem, é um piloto.

**Construção por pares casados (o truque metodológico):** para cada incidente, escrever duas descrições de arquitetura de ~300–500 palavras:

- **Caso-falha:** o estado *pré-incidente* do sistema, reconstruído do postmortem, contendo o risco causal mas **sem mencionar o incidente** nem dar pistas lexicais ("infelizmente", "o problema era").
- **Caso-gêmeo saudável:** a mesma arquitetura com a mitigação presente (idempotência adicionada, timeout configurado, DLQ existente). Tudo o mais idêntico.

O par casado controla confundidores: qualquer diferença de veredito entre gêmeos mede exatamente a capacidade de discriminar o risco, não o estilo do texto.

**Ground truth:** cada caso-falha recebe um rótulo de categoria causal da taxonomia abaixo (uma primária, opcionalmente uma secundária):

```
T01 retry sem idempotência        T07 falta de circuit breaker
T02 timeout ausente/mal calibrado  T08 falta de DLQ / mensagem perdida
T03 cache stampede / TTL           T09 esgotamento de pool/threads
T04 consistência eventual mal      T10 deploy sem rollback seguro
    tratada / dupla escrita        T11 dependência externa sem fallback
T05 retry storm / amplificação     T12 limite de capacidade / saturação
T06 hot partition / chave quente       não monitorada
```

**Higiene anti-vazamento:** reescrever os casos com nomes fictícios de serviços e domínios trocados (mesma técnica de blinding do livro). LLMs podem ter memorizado postmortems famosos; o sector-swap reduz o match por memorização.

## 2. Revisores sob teste (4 condições)

| ID | Revisor | O que prova |
|----|---------|-------------|
| R1 | **Naive** — "revise esta arquitetura e aponte problemas de confiabilidade" | baseline do mercado |
| R2 | **Contrato** — veredito estruturado + checklist FMEA por categoria + exigência de evidência citando o trecho | o tratamento; H1 prevê R2 > R1 |
| R3 | **Over-approver** (controle degenerado) — prompt enviesado a aprovar salvo falha óbvia | o eval precisa reprová-lo por recall baixo |
| R4 | **Over-flagger** (controle degenerado) — prompt enviesado a apontar todo risco concebível | **o controle mais importante**: terá recall alto e FP alto — prova que a métrica única engana e o *par* é necessário |

Mesmo modelo para todos (ex.: Sonnet) — isola o efeito do contrato/prompt, não do modelo. Temperatura fixa; 1 chamada por caso por revisor (piloto).

## 3. Métricas

- **Recall:** fração dos casos-falha em que o revisor emitiu CONCERN/FAIL **com categoria igual ao ground truth** (match de categoria, não menção vaga).
- **Taxa de FP:** fração dos gêmeos saudáveis em que o revisor emitiu CONCERN/FAIL **na categoria do ground truth do par** (penaliza alarme no risco já mitigado; achados em outras categorias são registrados à parte como *achados não solicitados*, para análise qualitativa).
- **Score de calibração (agregado):** recall − FP (índice de Youden). Um instrumento útil tem Youden alto; R3 e R4 devem ter Youden próximo de zero por caminhos opostos.

**Julgamento do match de categoria:** LLM-juiz com rubrica fechada (taxonomia + veredito do revisor → match S/N), com você auditando 100% dos julgamentos no piloto (n=120 julgamentos, ~1h). No piloto o humano é o juiz final; o LLM-juiz só acelera.

## 4. Critérios de decisão (definidos ANTES de rodar)

O experimento **corrobora H1** se, simultaneamente:
1. Recall(R2) ≥ Recall(R1) + 0,15 com FP(R2) ≤ FP(R1); e
2. R4 apresenta FP ≥ 0,40 (o eval pega o over-flagger); e
3. R3 apresenta Recall ≤ 0,40 (o eval pega o over-approver).

O experimento **falsifica H1** se R1 ≈ R2 (diferença < 0,10 em Youden) — o contrato não acrescenta nada mensurável — ou se os controles degenerados passam. Resultado intermediário: ajustar contrato/taxonomia e rodar segunda iteração antes de concluir.

## 5. Execução

1. Selecionar 15 postmortems com causa clara na taxonomia (meio dia de leitura).
2. Escrever os 15 pares blindados (1 dia — o maior custo do experimento).
3. Rodar `calib_experiment.py` (4 revisores × 30 casos = 120 chamadas; minutos, custo trivial).
4. Auditar julgamentos do juiz, calcular métricas, tabela final.
5. Decisão pelos critérios da seção 4.

**Custo total estimado:** ~2 dias de trabalho seu + centavos de API. Se corroborar, a tabela da seção 4 é o resultado central do paper (e o corpus vira ativo reutilizável — a Camada 4 nasce povoada). Se falsificar, você aprendeu por que o espaço estava vago antes de investir meses.

## 6. Ameaças à validade (declarar no paper)

- **n pequeno:** piloto direcional, não prova estatística — reportar intervalos, não p-valores triunfantes.
- **Memorização:** mitigada por blinding, não eliminada — declarar.
- **Autor único do corpus:** você escreve os pares conhecendo o ground truth; mitigação futura: segundo anotador independente.
- **Um modelo só:** generalização entre modelos fica para a fase 2.
