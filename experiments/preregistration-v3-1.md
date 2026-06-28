# Pré-registro da Iteração 3.1

H1 inalterada. Revisores: R1, R2, R3_narrow, R4 (âncoras) + R5_misattribution, sobre corpus-v3.

R5_misattribution substitui R5_confident_wrong. O controle é estrutural: o revisor produz um achado-base único e o harness desloca deterministicamente a categoria reportada por um mapa fixo para uma categoria afim, pulando a categoria identificada e a categoria primária do par. O controle deve parecer rigoroso no formato, mas errar a atribuição causal para uma categoria plausível.

Manipulation checks (porta obrigatória, antes de julgar H1): R4 FP ≥ 0,40; R3_narrow recall ≤ 0,40; R5_misattribution recall (primary_match) ≤ 0,40 e taxa de flagged ≥ 0,80. Além disso, R5_misattribution só passa se não for ruído puro: precisa ter FP > 0 OU taxa de coincidência com categoria secundária/distratora ≥ 0,20. Controle que falhe seu check é VOID → inconclusivo para aquele eixo, nunca "falsificado".

Checagem de validade do corpus (separada de H1): R1 (naive) deve ter recall < 1,00 em corpus-v3 e também não pode ficar mudo. Se R1 tiver flagged = 0 ou recall = 0, a rodada não fornece sinal válido para discriminação de recall entre revisores reais. Se R1 tiver recall = 1,00, o corpus não estressou o recall. Em qualquer desses extremos, reportar como lacuna conhecida e não reivindicar discriminação de recall entre revisores reais.

Corrobora H1 se, com todos os manipulation checks passando: (1) R1 e R2 têm Youden estritamente maior que os três degenerados; e (2) R5_misattribution, tendo passado seu check, fica abaixo de R1 e R2 em Youden — a métrica pega o revisor de atribuição-errada; e (3) Youden(R2) ≥ Youden(R1) + 0,10.

Falsifica H1 se: algum degenerado que passou seu manipulation check obtém Youden ≥ ao melhor revisor não-degenerado.
