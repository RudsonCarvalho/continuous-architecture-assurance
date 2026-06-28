# corpus-v3 manifest

Status geral: draft-needs-human-review. Estes 20 pares sao candidatos para a iteracao 3 e nao devem ser tratados como ground truth validado ate revisao humana.

Objetivo: dessaturar recall com sinais arquiteturais mais sutis, mantendo blindagem anti-vazamento. Cada caso usa nomes ficticios e troca de dominio. O campo `distractor_category` registra uma causa plausivel porem falsa inserida para testar raciocinio.

## Pares e justificativas

| Pair | Status | Ground truth | Distractor | Public source basis | Justificativa do ground truth |
|---|---|---|---|---|---|
| V3-01 | draft-needs-human-review | T12 | T02 | AWS EC2 DNS Seoul resolver capacity summary | O mecanismo de falha envolve reducao efetiva de fleet abaixo da demanda regional; timeouts aparecem como sintoma. |
| V3-02 | draft-needs-human-review | T04 | T10 | CircleCI Nov 2021 incompatible schema deploy | Mantido como T04: o texto agora deixa o deploy plausivel, mas o mecanismo central e coexistencia de formatos escritos/lidos de modo incompatível. |
| V3-03 | draft-needs-human-review | T03 | T10 | Cloudflare Tiered Cache outage summary | Objetos criados em janelas parecidas envelhecem juntos e fazem muitas leituras chegarem ao mesmo caminho regional; o release segue como distrator plausivel. |
| V3-04 | draft-needs-human-review | T02 | T11 | GitHub DNS outage postmortem | A dependencia de resolucao permanece plausivel, mas o mecanismo dominante e a janela longa por etapa ocupando workers e acumulando operacoes bloqueadas. |
| V3-05 | draft-needs-human-review | T04 | T07 | GitHub Oct 2018 database partition analysis | Escritas concorrentes em regioes diferentes produzem historicos validos e divergentes sem token global de epoca. |
| V3-06 | draft-needs-human-review | T09 | T12 | AWS Kinesis Nov 2020 event summary | Unidade de trabalho por shard segura threads ate callbacks; dashboards agregados nao mostram ocupacao do pool. |
| V3-07 | draft-needs-human-review | T10 | T12 | Cloudflare July 2019 WAF outage | Reclassificado: o mecanismo decisivo foi distribuicao global sem rollout em estagios; a remediacao primaria da Cloudflare foi rollout escalonado. Saturacao de CPU e consequencia, nao causa raiz. |
| V3-08 | draft-needs-human-review | T05 | T09 | CircleCI queue backlog incident summaries | Tentativas por job crescem mais rapido que jobs distintos durante recuperacao, mantendo T09 como distrator operacional. |
| V3-09 | draft-needs-human-review | T06 | T12 | Foursquare/MongoDB sharding outage summaries | Uma chave logica de tenant concentra escritas em um shard enquanto o cluster agregado conserva margem. |
| V3-10 | draft-needs-human-review | T07 | T11 | GoCardless database cluster outage summaries | O componente de descoberta fica degradado e a API segue chamando sem estado local de circuito aberto. |
| V3-11 | draft-needs-human-review | T01 | T04 | Twilio Billing Incident Post-Mortem | Fonte nominal substituida por postmortem publico da Twilio; o caso preserva recargas repetidas quando o saldo nao e atualizado e falta de chave unica da tentativa original. |
| V3-12 | draft-needs-human-review | T10 | T04 | Rust crates.io deploy/download outage | Referencias persistentes sao publicadas no formato novo antes de existir reversao/traducao segura. |
| V3-13 | draft-needs-human-review | T11 | T02 | PagerDuty DNS/container orchestration DNS config incident | Timeouts aparecem nos logs, mas a indisponibilidade do resolvedor externo bloqueia bootstrap e recuperacao de servicos. |
| V3-14 | draft-needs-human-review | T08 | T05 | Allegro asynchronous task-processing outage summary | Mensagens com erro inesperado sao descartadas sem DLQ nem replay auditavel, enquanto reenvios de clientes ficam plausiveis. |
| V3-15 | draft-needs-human-review | T10 | T12 | TravisCI image cleanup/config rollback incidents | Artefatos antigos sao removidos antes de validacao ampla da nova imagem, impossibilitando retorno simples. |
| V3-16 | draft-needs-human-review | T02 | T07 | Mozilla Firefox Proxy Failover incident | Fonte atualizada para incidente nominal; o fluxo aguarda uma fase sem deadline curto antes do fallback. |
| V3-17 | draft-needs-human-review | T06 | T09 | GitHub ProxySQL/mysql1 load incidents | Consultas pesadas de uma unica organizacao concentram calor no mesmo destino, com conexoes presas como sintoma. |
| V3-18 | draft-needs-human-review | T05 | T01 | GitHub App permissions retry-on-timeout incident summary | O token e deterministico, mas cada timeout abre nova consulta cara e aumenta concorrencia no mesmo backend. |
| V3-19 | draft-needs-human-review | T09 | T12 | Val Town Sep 2024 outage postmortem | Traces mostram tempo longo dentro da janela transacional antes das escritas, enquanto CPU e SQL individual seguem moderados; capacidade agregada permanece distrator. |
| V3-20 | draft-needs-human-review | T11 | T10 | Salesforce policy/resource access disruption summaries | Mudanca recente e plausivel como deploy, mas varias aplicacoes dependem em tempo real do servico central sem cache/fallback. |

## Autoauditoria de vazamento

| Pair | Status | Vazamento removido? | Distrator preservado? | Observacao |
|---|---|---|---|---|
| V3-01 | draft-needs-human-review | Sim | Sim | Mecanismo de capacidade implicita, sintomas de timeout ainda plausiveis. |
| V3-02 | draft-needs-human-review | Sim | Sim | Rótulo T04 mantido; deploy segue plausivel. |
| V3-03 | draft-needs-human-review | Sim | Sim | Mecanismo distribuido entre TTL comum, envelhecimento conjunto e leitura regional; sem frase unica que entregue a causa. |
| V3-04 | draft-needs-human-review | Sim | Sim | T02 ficou primario por prazos longos em varias etapas; DNS permanece como distrator secundario. |
| V3-05 | draft-needs-human-review | Sim | Sim | Bloqueio de trafego/circuit breaker segue leitura possivel. |
| V3-06 | draft-needs-human-review | Sim | Sim | Segue o padrao do exemplo: threads por shard e dashboards agregados. |
| V3-07 | draft-needs-human-review | Sim | Sim | Rotulo resolvido para T10; T12 preservado como consequencia/distrator. |
| V3-08 | draft-needs-human-review | Sim | Sim | Workers ocupados preservam distrator T09. |
| V3-09 | draft-needs-human-review | Sim | Sim | Capacidade agregada preservada como leitura plausivel. |
| V3-10 | draft-needs-human-review | Sim | Sim | Dependencia interna sem fallback permanece plausivel. |
| V3-11 | draft-needs-human-review | Sim | Sim | Fonte nominal resolvida com postmortem da Twilio; ajuste minimo para alinhar ao incidente. |
| V3-12 | draft-needs-human-review | Sim | Sim | Metadados persistentes preservam distrator T04. |
| V3-13 | draft-needs-human-review | Sim | Sim | Timeouts de inicializacao preservam distrator T02. |
| V3-14 | draft-needs-human-review | Sim | Sim | Reenvios de clientes preservam distrator T05. |
| V3-15 | draft-needs-human-review | Sim | Sim | Filas de builders preservam distrator T12. |
| V3-16 | draft-needs-human-review | Sim | Sim | Flag operacional preserva distrator T07. |
| V3-17 | draft-needs-human-review | Sim | Sim | Conexoes presas preservam distrator T09. |
| V3-18 | draft-needs-human-review | Sim | Sim | Token deterministico preserva distrator T01 sem confirmar causa. |
| V3-19 | draft-needs-human-review | Sim | Sim | Sinais agora ficam em traces e dashboards agregados; CPU moderada/capacidade historica preservam distrator T12. |
| V3-20 | draft-needs-human-review | Sim | Sim | Mudanca recente preserva distrator T10. |

## Fontes abertas consultadas

- https://github.com/danluu/post-mortems
- https://aws.amazon.com/message/74876-2/
- https://discuss.circleci.com/t/incident-report-november-8-2021-jobs-stuck-in-a-not-running-state/41890
- https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/
- https://aws.amazon.com/message/11201/
- https://github.blog/news-insights/company-news/oct21-post-incident-analysis/
- https://github.blog/news-insights/the-library/dns-outage-post-mortem/
- https://www.twilio.com/en-us/blog/company/communications/billing-incident-post-mortem-breakdown-analysis-and-root-cause-html
- https://hacks.mozilla.org/2022/01/heads-up-fx-96-tab-crash-on-linux/
- https://blog.val.town/blog/first-postmortem/
