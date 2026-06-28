# Pré-registro da Iteração 2

H1 (inalterada): a métrica pareada recall/FP discrimina revisores bons de ruins.

Manipulation check (porta obrigatória): antes de julgar H1, cada controle degenerado deve provar que é degenerado. R4 deve ter FP ≥ 0,40; R3_narrow deve ter recall ≤ 0,40. Se um controle falhar seu manipulation check, esse braço é VOID e o resultado é INCONCLUSIVO para aquele eixo — nunca "falsificado".

Corrobora H1 se, com ambos os manipulation checks passando: (1) R3_narrow tem FP ≤ 0,20 e recall ≤ 0,40 — confirmando que é um revisor que o FP-sozinho aprovaria mas o par pega pelo recall; e (2) tanto R1 quanto R2 têm Youden estritamente maior que ambos os degenerados; e (3) Youden(R2) ≥ Youden(R1) + 0,10.

Falsifica H1 se: algum controle degenerado, tendo passado seu manipulation check, obtém Youden ≥ ao melhor revisor não-degenerado.
