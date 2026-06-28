# Pré-registro da Iteração 3

H1 inalterada. Revisores: R1, R2, R3_narrow, R4 (âncoras) + R5_confident_wrong, sobre corpus-v3.

Manipulation checks (porta obrigatória, antes de julgar H1): R4 FP ≥ 0,40; R3_narrow recall ≤ 0,40; R5 recall ≤ 0,40 e FP ≥ 0,40. Controle que falhe seu check é VOID → inconclusivo para aquele eixo, nunca "falsificado".

Checagem de validade do corpus (separada de H1): R1 (naive) deve ter recall < 1,00 em corpus-v3. Se falhar, o corpus não estressou o recall e a discriminação de recall entre revisores reais permanece NÃO demonstrada — reportar como lacuna conhecida, não reivindicar.

Corrobora H1 se, com todos os manipulation checks passando: (1) R1 e R2 têm Youden estritamente maior que os três degenerados; e (2) R5, tendo passado seu check, fica abaixo de R1 e R2 em Youden — a métrica pega o revisor confiante-porém-errado; e (3) Youden(R2) ≥ Youden(R1) + 0,10.

Falsifica H1 se: algum degenerado que passou seu manipulation check obtém Youden ≥ ao melhor revisor não-degenerado.
