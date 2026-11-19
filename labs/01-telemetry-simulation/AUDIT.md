# S01 — auditoria dos critérios de conclusão

**Data da auditoria:** 19/11/2026  
**Base examinada:** branch `main`, commit `87f39d83396260cdbe515cde59db3bf9c3948280` (antes das correções documentais desta auditoria).  
**Escopo:** exclusivamente a simulação local de telemetria S01, documentação e evidências do GitHub Actions. **Não inclui** FlatSat físico, sensores, UART/USB, RF, GSE, Yamcs, observabilidade integrada ou S05.

## Parecer executivo

**Resultado: aprovado tecnicamente para continuidade, mas não encerrado formalmente.**

A cadeia sintética `geração → registro dos bytes → validação CRC e sequência → gabarito separado → avaliação → SHA-256 recalculado → replay` está implementada, possui resultados reproduzíveis e foi exercitada pelo CI. O status **Em desenvolvimento** permanece apropriado até completar o registro permanente e a avaliação explícita dos critérios finais do S01. Não há fundamento para declarar confiabilidade operacional de um satélite ou classificador de causas de falhas.

## Evidências examinadas

- [Execução GitHub Actions #44628393863](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44628393863) — conclusão `success` para o commit-base `87f39d8`.
- [Execução #44628209124](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44628209124) — **70 testes aprovados**; cinco cenários conformes, cinco auditorias de SHA-256 e cinco reproduções de eventos correspondentes.
- [Artefato da execução #44628209124](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44628209124/artifacts/14581060691) — ZIP com 19 arquivos, ID `14581060691`, expiração prevista no GitHub em **03/12/2026 22:23:51 UTC**.
- **SHA-256 do ZIP examinado:** `11986c730e4e9102b930dbbdca42fa4a04c36515204fc08f0830e73cdf3be47c`.
- Auditoria adicional do ZIP: hashes dos cinco conjuntos conferidos com os dois relatórios; quadro `corrupt` apresenta **um CRC inválido**, enquanto os demais quadros estão íntegros.

## Matriz de verificação do S01

| Critério | Resultado | Fundamento e limite |
|---|---|---|
| Identificação de origem sintética e escopo | **Atendido** | `data_origin=synthetic`, formato de 12 bytes, sem alegação CCSDS ou enlace físico |
| Pacotes versionados, sequência, grandezas e CRC | **Atendido** | `packet.py`, vetor CRC e testes de limites |
| Cinco cenários determinísticos | **Atendido** | `baseline`, `drop`, `duplicate`, `reorder`, `corrupt` |
| Registro do gabarito separado das observações | **Atendido com limite** | Arquivos e fluxo distintos, gerados dentro do mesmo simulador |
| Metadados, hashes e entradas preservadas | **Atendido para execuções novas** | `run_id`, timestamps UTC, commit, Python, quadros em hexadecimal; o runner legado não arquiva os quadros |
| Integridade de quadros e CRC | **Atendido** | Auditoria dos bytes e rejeição da corrupção prevista |
| Replay dos eventos e contadores | **Atendido com limite** | Cinco replays correspondentes; utiliza o mesmo decoder e `SequenceTracker` |
| Testes automatizados e integração contínua | **Atendido** | 70 testes e cinco cenários conformes no CI, com execução confirmada |
| Evidência preservada no histórico Git | **Atendido após esta auditoria** | ZIP original da execução, manifesto SHA-256 e verificador em `evidence/reference-v1/`; disponibilidade depende do repositório |
| Hipótese experimental e critérios finais de aceite próprios do S01 | **Parcial** | Há objetivos, políticas esperadas e testes, mas falta um quadro de encerramento restrito ao S01 |
| Status coerentes nos documentos do repositório | **Correção nesta auditoria** | READMEs PT/EN e roadmap ainda classificavam S01 como planejado |
| Ensaios estatísticos e diagnóstico independente de causas | **Fora do aceite do S01 inicial** | Pertencem à evolução da metodologia e/ou ao S05; não devem ser reivindicados nesta versão |
| Hardware, serial, RF, GSE, Yamcs e observabilidade | **Fora do escopo atual** | Dependem de outros laboratórios e validações específicas |

## Pendências priorizadas

**P1 — Preservação durável de evidência representativa (resolvida após a auditoria).** O ZIP original de 19 arquivos foi revisado e incorporado ao histórico Git com manifesto de SHA-256 e verificador reproduzível em `evidence/reference-v1/`. A disponibilidade depende da manutenção do repositório.

**P1 — Aceite científico delimitado.** Escrever explicitamente, na documentação do S01, a hipótese verificável, o objeto da verificação (software didático) e a condição para declarar *concluída a iteração v1 de software*, separada de metas futuras de hardware ou classificação causal.

**P2 — Consistência entre documentos.** Corrigir status S01 nas páginas principais PT/EN e no roadmap; distinguir simulação já executada da arquitetura física prevista. Ajuste documental efetuado junto a este parecer.

**P3 — Limpeza documental de baixo impacto.** Verificar o arquivo placeholder `images` no diretório do S01 (não é um diretório de imagens) e melhorar pequenas redações históricas que possam sugerir pendência de uma execução CI já validada. Não altera resultados.

## Decisão sobre o encerramento

- **Aprovado:** continuar usando o S01 como base didática de geração, integridade e validação de pacotes sintéticos.
- **Não aprovado:** declarar que o S01 valida FlatSat físico, GSE, RF, telemetria orbital, taxa real de perda ou acurácia de classificação causal.
- **Status recomendado:** **Em desenvolvimento**, pois resta formalizar a hipótese experimental e o aceite científico restrito à iteração v1. A preservação da evidência foi atendida posteriormente.
- **Próximo incremento objetivo:** revisar e publicar **uma execução de referência estável**, acompanhada de manifesto com SHA-256 e link ao commit que a produziu. Não são necessárias integrações com hardware para concluir essa tarefa.

> Este parecer baseia-se nos arquivos do repositório e nos registros de execução identificados acima. Uma execução bem-sucedida do mesmo software não demonstra, isoladamente, correção formal do algoritmo, independência científica do gabarito ou qualidade de dados reais.
