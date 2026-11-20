# S01 — aceite técnico da iteração v1 de software

**Data do parecer:** 20/11/2026  
**Versão avaliada:** v1, simulação determinística de telemetria local  
**Commit-base examinado:** `7adf36d9b7f3063166f0a2a3169837712e0504c2` (`main`)  
**Decisão:** **ACEITA — somente a iteração v1 de software, nos limites descritos a seguir.**  
**Situação do laboratório S01:** **Em desenvolvimento.**

## 1. Objeto e fronteira do aceite

O aceite trata de um **simulador local e didático em Python**, sem bibliotecas
externas, para gerar quadros de telemetria sintética, conferir CRC-16/CCITT-FALSE,
acompanhar sequências, introduzir intervenções conhecidas no gerador e avaliar
a integridade e a reprodutibilidade dos registros.

Não compreende qualificação de firmware, aquisição real de sensores, FlatSat
físico, enlace serial ou de radiofrequência, Ground Support Equipment, Yamcs,
telemetria orbital ou diagnóstico independente da causa de falhas. Esses são
objetivos de outros laboratórios ou de futuras iterações.

A palavra **aceita** significa conformidade funcional com os critérios abaixo,
observada em casos de teste previamente estruturados. **Não** significa
certificação, homologação, validação estatística ou conclusão do projeto espacial.

## 2. Questão e hipótese técnica verificável

**Questão de engenharia:** é possível, utilizando somente Python e um formato
experimental de quadro, reproduzir de maneira determinística as observações
de integridade e sequência previstas para cinco cenários sintéticos controlados,
sem fornecer ao receptor os rótulos de intervenção do gerador, e preservar dados
suficientes para auditar bytes e eventos posteriormente?

**Hipótese operacional H1:** nos cinco cenários especificados em
[`evaluation_policy.json`](evaluation_policy.json), a cadeia
`geração → recepção/CRC → observação → gabarito separado → avaliação →
arquivamento de bytes → SHA-256 → replay` apresenta:
- cinco avaliações `conformant` e nenhum `deviation` ou `inconsistent`;
- cinco conjuntos de bytes `verified` e nenhum `failed`;
- cinco replays `matched` e nenhum `mismatch` ou `unverifiable`;
- suíte automatizada aprovada na execução de referência.

**Critério de não atendimento:** qualquer resultado inesperado nos cenários
fixos, divergência nos registros ou falha na suíte invalida o aceite dessa
iteração até investigação e nova execução documentada.

Trata-se de **hipótese funcional determinística**, não de hipótese estatística
com inferência populacional. A política de expectativas foi versionada antes
da execução de referência, mas este documento de aceite foi consolidado
**após** a implementação e os testes; não é um pré-registro de pesquisa.

## 3. Entradas, ambiente e procedimentos

- **Dados:** exclusivamente sintéticos, `data_origin=synthetic`.
- **Quadro v1:** 12 bytes em big-endian, prefixo `TS`, versão, fonte,
  sequência de 16 bits, tensão em mV, temperatura em centésimos de °C
  e CRC-16/CCITT-FALSE; não é um quadro CCSDS ou AX.25.
- **Cenários:** `baseline`, `drop`, `duplicate`, `reorder` e `corrupt`.
  A sequência de referência é `0, 1, 2, 3, 4`; cada cenário aplica uma
  alteração fixa, com gabarito do gerador em arquivo distinto.
- **Ambiente observado:** runner Linux hospedado pelo GitHub, Python 3.13,
  apenas biblioteca padrão do Python.
- **Registros:** identificador de execução, cenários, parâmetros, origem dos
  dados, timestamps UTC, commit quando disponível, contagens, eventos, SHA-256,
  quadros entregues ao receptor e limitações.
- **Integridade:** SHA-256 dos quadros na ordem de recepção, precedendo cada
  quadro por seu comprimento `uint32` big-endian. O hash não é assinatura.
- **Reprodução:** o replay usa o mesmo `packet.py` e `SequenceTracker`,
  mas não reutiliza `build_report` nem consulta o gabarito.

### Procedimento reexecutável

A partir de `labs/01-telemetry-simulation`:

```bash
python -m unittest discover -s tests -v
python verify_reference_snapshot.py
python run_scenarios.py --run-id s01-aceite-v1-local-001
python verify_evidence.py run-artifacts/s01-aceite-v1-local-001
python replay_observations.py run-artifacts/s01-aceite-v1-local-001
python evaluate_scenarios.py run-artifacts/s01-aceite-v1-local-001
```

O identificador deve ser alterado em novas execuções; os arquivos anteriores
não são sobrescritos. O workflow
[`s01-validation.yml`](../../.github/workflows/s01-validation.yml)
automatiza esse procedimento, usando seu próprio `run_id`.

## 4. Matriz de requisitos e decisão

| ID | Critério de aceite da v1 | Evidência verificável | Resultado |
|---|---|---|---|
| AC-01 | Formato de 12 bytes, campos e unidades explícitos; CRC verificado com vetor conhecido e dados inválidos rejeitados | `packet.py`, `tests/test_packet.py` | **Atendido** |
| AC-02 | Cinco cenários determinísticos com intervenções registradas no gerador | `scenarios.py`, `tests/test_scenarios.py` | **Atendido** |
| AC-03 | Rótulos da intervenção ausentes da entrada do receptor; observações separadas do gabarito | `run_scenarios.py`, `observations.json`, `ground_truth.json` | **Atendido, com limite** |
| AC-04 | Cinco resultados conformes com a política de expectativas, sem divergências nem registros inconsistentes | `evaluation_policy.json`, `evaluation.json` | **Atendido (5/5)** |
| AC-05 | Quadros recebidos preservados e integridade SHA-256 recalculável | `input_frames.json`, `verify_evidence.py`, `evidence_verification.json` | **Atendido (5/5)** |
| AC-06 | Reprodução dos eventos e contadores originais a partir dos bytes arquivados | `replay_observations.py`, `replay_verification.json` | **Atendido (5/5), com limite** |
| AC-07 | Testes automatizados e cadeia integrada executados com sucesso em CI | GitHub Actions #44638911211, commit-base | **Atendido (76/76)** |
| AC-08 | Evidência de referência preservada no Git com manifesto, hash e verificações automáticas | `evidence/reference-v1/`, `verify_reference_snapshot.py` | **Atendido** |
| AC-09 | Registro explícito de limitações e rejeição de alegações não sustentadas | `README.md`, `VALIDATION.md`, `AUDIT.md` e este documento | **Atendido** |

**Observação sobre AC-03:** o gabarito não é usado como entrada do receptor,
mas a geração e a recepção ainda pertencem a uma mesma simulação local.
A separação é de fluxo de dados, **não uma fonte física ou experimentalmente
independente**.

**Observação sobre AC-06:** a reprodução demonstra que o mesmo algoritmo
obtém resultados iguais com entradas arquivadas. Não representa uma
implementação independente que certifique a correção de `SequenceTracker`.

## 5. Resultados observados nos cinco cenários

| Cenário | Quadros entregues | Inválidos por CRC | Lacunas observadas | Duplicados | Fora de ordem |
|---|---:|---:|---:|---:|---:|
| `baseline` | 5 | 0 | 0 | 0 | 0 |
| `drop` | 4 | 0 | 1 | 0 | 0 |
| `duplicate` | 6 | 0 | 0 | 1 | 0 |
| `reorder` | 5 | 0 | 1 | 0 | 1 |
| `corrupt` | 5 | 1 | 1 | 0 | 0 |

Os cinco cenários tiveram resultado `conformant`, os cinco hashes foram
recalculados com sucesso e os cinco replays corresponderam aos registros
originais. Uma **lacuna de sequência não é prova de perda física**: no caso
`reorder`, todos os quadros de origem foram entregues, mas uma lacuna
aparece temporariamente. Em `corrupt`, o CRC rejeita o quadro adulterado;
isso não identifica uma causa física de corrupção.

As 76 verificações aprovadas correspondem a uma suíte de regressão
e integração; **não equivalem a 76 ensaios independentes de telemetria**
ou a uma estimativa de cobertura de código ou confiabilidade estatística.

## 6. Evidências de proveniência e rastreabilidade

- **Último commit-base conferido antes deste parecer:**
  [`7adf36d9b7f3063166f0a2a3169837712e0504c2`](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/commit/7adf36d9b7f3063166f0a2a3169837712e0504c2).
- **Execução aprovada do commit-base:** [GitHub Actions #44638911211](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44638911211), `success`.
- **Execução que originou o conjunto histórico preservado:**
  [#44628209124](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44628209124),
  commit `ac233f6ad9d227ef22c1b144350c1659722c9767`,
  70 testes naquela versão, cinco cenários conformes.
- **Evidência de referência preservada:** [`evidence/reference-v1/`](evidence/reference-v1/README.md);
  ZIP original e `manifest.json` com SHA-256 do pacote e dos 19 arquivos internos.
- **Validação do snapshot de referência:** [#44638754042](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44638754042),
  com 76 testes aprovados e manifesto conferido.
- **Auditoria anterior:** [`AUDIT.md`](AUDIT.md) e registros históricos
  de [`VALIDATION.md`](VALIDATION.md).

**Distinção de versões:** a execução histórica arquivada não foi
regenerada nem reatribuída ao commit posterior. A suíte moderna
valida o snapshot congelado e reexecuta o pipeline de software em
novas execuções independentes de diretório.

## 7. Limitações científicas e compromissos futuros

O aceite não sustenta estimativas de precisão, sensibilidade, recall,
taxa real de perda, taxa de falsos positivos, desempenho em campo,
resistência à radiação, confiabilidade de hardware ou segurança de voo.
Os casos são fixos e didáticos, sem amostragem aleatória ou repetições
independentes. O CRC detecta as alterações exercitadas, não todas as
alterações possíveis. SHA-256 detecta mudanças não coordenadas, mas
não autentica a origem sem mecanismos adicionais.

A integração com interfaces serial/USB, FlatSat físico, instrumentação,
GSE, Yamcs, observabilidade e engenharia do caos pertence a
etapas posteriores. A avaliação comparativa de causas de falha pertence
a um estudo futuro, associado ao S05, e exige métodos independentes,
planejamento experimental específico e tratamento estatístico adequado.

## 8. Decisão de aceite e estado do laboratório

**Parecer:** os requisitos AC-01 a AC-09 foram atendidos no escopo
restrito desta avaliação. Portanto, a **iteração v1 de software
de simulação de telemetria está tecnicamente aceita** como referência
didática reproduzível.

**Estado do S01:** permanece **Em desenvolvimento**, pois o laboratório
pode incluir refinamentos de experimentação e integração em outras
fases. O aceite de um incremento versionado **não implica conclusão
de toda a trilha S01** nem altera o status de S00 ou S02–S08.

Esta decisão é um registro técnico do próprio projeto, baseado em
testes e evidências automatizadas, e **não constitui homologação
ou certificação por terceira parte**. Mudanças posteriores de código
devem ser verificadas nos próprios commits e execuções de CI;
não ficam automaticamente abrangidas por este parecer.
