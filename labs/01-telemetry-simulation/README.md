# S01 — Simulação e integridade da telemetria

**Situação:** Em desenvolvimento — implementação e cenários controlados de software testados.

## Objetivo

Gerar quadros sintéticos de telemetria, validar sua integridade e analisar o comportamento de um receptor diante de sequências normais, perdas estimadas, duplicações, reordenação e corrupção de dados.

Esta primeira iteração é **exclusivamente uma simulação local em Python**. Não utiliza hardware, canal de rádio, estação terrestre ou dados orbitais reais. O formato binário é didático e **não declara conformidade com CCSDS, AX.25 ou outros protocolos espaciais**.

## Implementação disponível

| Arquivo | Finalidade |
|---|---|
| `packet.py` | Codificador e decodificador de quadros, CRC-16 e observação de sequência por fonte |
| `demo.py` | Demonstração determinística de recepção, lacuna, duplicação, reordenação e corrupção |
| `run_experiment.py` | Execução do cenário legado de referência com relatório JSON individual |
| `scenarios.py` | Gerador de cinco cenários determinísticos e gabarito das intervenções |
| `run_scenarios.py` | Execução de um ou cinco cenários, separando observações e gabarito em arquivos JSON |
| `tests/test_scenarios.py` | Testes da separação dos registros, dos resultados e da prevenção de sobrescrita |
| `frame_evidence.py` | Arquiva os bytes pós-intervenção entregues ao receptor em hexadecimal |
| `replay_observations.py` | Reproduz eventos e contadores diretamente dos quadros arquivados |
| `tests/test_replay_observations.py` | Testes de replay e de alterações coordenadas de quadros e hashes |
| `verify_evidence.py` | Recalcula SHA-256 independentemente da geração, comparando-o aos relatórios |
| `tests/test_frame_evidence.py` | Detecta alteração, reordenação, truncamento, metadados inconsistentes e sobrescrita |
| `evaluation_policy.json` | Política versionada com contadores, estados e intervenções esperados para os cinco cenários |
| `evaluate_scenarios.py` | Avaliador pós-execução: consistência, conformidade e tabela-resumo |
| `tests/test_evaluate_scenarios.py` | Testes de conformidade, divergência, inconsistência e bloqueio de sobrescrita |
| `tests/test_experiment.py` | Testes do relatório, contadores, SHA-256 e proteção contra sobrescrita |
| `tests/test_packet.py` | Testes automatizados offline com a biblioteca padrão `unittest` |

### Quadro experimental v1

Todos os campos são codificados em **big-endian**, com tamanho fixo de **12 bytes**.

| Campo | Bytes | Representação |
|---|:---:|---|
| Magic | 2 | ASCII `TS` |
| Versão | 1 | `1` |
| Identificador da fonte | 1 | Inteiro de 0 a 255 |
| Número de sequência | 2 | Inteiro sem sinal de 0 a 65535, com retorno a zero |
| Tensão de bateria | 2 | Inteiro sem sinal, em milivolts (`battery_mv`) |
| Temperatura | 2 | Inteiro com sinal, em centésimos de °C (`temperature_centi_c`) |
| CRC | 2 | CRC-16/CCITT-FALSE sobre os dez bytes anteriores |

Parâmetros do CRC: polinômio `0x1021`, inicialização `0xFFFF`, entrada e saída sem reflexão, `xorout=0`. O vetor público de verificação `123456789` deve resultar em `0x29B1`.

A identificação do ensaio (`run_id`) e a origem dos dados (`data_origin=synthetic`) são metadados de execução, não campos do quadro v1. Valores numéricos usados na demonstração são **sintéticos**, não leituras de sensores.

### Interpretação de sequência

Após validação de formato e CRC, a classe `SequenceTracker` acompanha cada fonte separadamente:

- `first`: primeiro quadro válido observado da fonte;
- `in_order`: sequência consecutiva, incluindo o retorno de `65535` para `0`;
- `gap`: avanço de sequência com lacuna; `estimated_missing` contém a quantidade inferida;
- `duplicate`: repetição da última sequência aceita;
- `out_of_order`: número anterior ou salto ambíguo.

A classificação de avanço é limitada a distâncias menores que metade do espaço de sequência (`32768`). Saltos maiores ou iguais a esse limite são tratados como ambíguos, sem declarar perda. Quadros duplicados ou fora de ordem não avançam a referência. Quadros inválidos são rejeitados antes da análise de sequência.

**Limitações:** lacunas não provam perda em um enlace físico; reinicializações do emissor, reordenação, ausência de sincronização e múltiplas voltas do contador exigem tratamentos adicionais. O CRC detecta muitas alterações acidentais, mas não todas, e não fornece autenticidade criptográfica.

## Como executar

Requisito: Python **3.10 ou posterior**. Não há bibliotecas de terceiros nem recursos em nuvem.

A partir do diretório do laboratório `labs/01-telemetry-simulation`:

```bash
python demo.py
python -m unittest discover -s tests -v
```

No Windows, se o comando `python` não estiver disponível, use o Python Launcher (`py`) nos mesmos comandos.

A demonstração imprime a origem sintética, valores de sequência, classificações e um quadro corrompido rejeitado por CRC. O fluxo (sequências `0, 1, 3, 3, 2, 4`) é fixo para permitir a reprodução do resultado. Nenhum arquivo ou serviço externo é alterado.

### Registro estruturado de execuções (cenário de referência)

O comando abaixo processa os mesmos quadros sintéticos do exemplo e salva um relatório JSON, com identificador único gerado automaticamente:

```bash
python run_experiment.py
```

Para atribuir um identificador próprio ou escolher um diretório de saída:

```bash
python run_experiment.py --run-id s01-verificacao-001 --output-dir run-artifacts
```

Por padrão, os relatórios são gravados em `run-artifacts/<run_id>.json`, pasta local ignorada pelo Git. Arquivos já existentes **não são sobrescritos**. Revise e remova informações sensíveis antes de publicar qualquer artefato de execução. A estrutura inclui `schema_version`, `run_id`, `lab_id`, `scenario_id`, `utc_start`, `utc_end`, `data_origin`, `git_commit` (quando disponível), `firmware_version`, ambiente Python, `params`, `measurements`, `events`, `checksums` e limitações.

O hash SHA-256 é calculado sobre a concatenação ordenada de cada quadro precedido de seu comprimento em quatro bytes big-endian. Para a entrada sintética da primeira iteração, o hash esperado é `d665a7deb1c8820c4c4f6449c9199caddcc5100f1a68374604886741b33c7528`.

**Valores observados no cenário local:** sete quadros processados, seis válidos, um rejeitado por CRC, uma lacuna de sequência (um quadro estimado), uma duplicação e um quadro fora de ordem. A sequência `2` aparece tardiamente: **não se conclui que houve perda efetiva de quadro**. A referência de execução é determinística, mas os horários e o identificador variam entre execuções. O relatório de eventos é uma observação do próprio decodificador, não uma fonte independente de verdade para ensaios comparativos.

### Matriz de cinco cenários controlados (software)

Os ensaios seguintes utilizam a mesma fonte sintética e a sequência de referência `0, 1, 2, 3, 4`. Não representam medições sobre RF, FlatSat físico, GSE ou satélites reais.

| Cenário | Intervenção conhecida pelo gerador | Observação do receptor |
|---|---|---|
| `baseline` | Nenhuma | Cinco quadros válidos, em ordem |
| `drop` | Omitir quadro 2 antes de entregá-lo ao receptor | Uma lacuna, 1 quadro estimado ausente |
| `duplicate` | Repetir quadro 2 | Um quadro duplicado |
| `reorder` | Trocar as posições dos quadros 2 e 3 | Uma lacuna e um quadro fora de ordem, **sem perda real injetada** |
| `corrupt` | Inverter um bit do quadro 2 sem recalcular o CRC | Um quadro inválido por CRC e uma lacuna posterior |

Execute os cinco cenários:

```bash
python run_scenarios.py
```

Ou selecione apenas um cenário e um identificador próprio:

```bash
python run_scenarios.py --scenario reorder --run-id s01-reorder-001
```

A saída padrão é `run-artifacts/<run_id>/<scenario>/`, contendo:

- `observations.json` — classificações e contadores produzidos exclusivamente por `decode_packet` e `SequenceTracker`, sem entrada do gabarito;
- `ground_truth.json` — metadados da geração e a intervenção controlada conhecida **somente pelo gerador**;
- `input_frames.json` — representação hexadecimal dos **quadros realmente apresentados ao receptor**, na ordem recebida e após a intervenção sintética.

Os dois arquivos compartilham `run_id`, `scenario_id` e `checksums.input_frames_sha256`, para auditoria do mesmo conjunto ordenado de quadros. Os resultados são gravados em novos diretórios de execução; um `run_id` existente provoca erro, sem sobrescrever os arquivos anteriores. O diretório padrão `run-artifacts/` é ignorado pelo Git.

**Interpretação científica:** a lacuna detectada em `reorder` não deve ser contabilizada como perda efetiva; já em `drop` a omissão é comprovada apenas pelo gabarito do gerador, não pela observação do receptor. A corrupção demonstra rejeição por CRC, mas não identifica, isoladamente, a causa física de uma alteração. O hash é uma verificação de integridade/reprodutibilidade, não uma comprovação de autenticidade.

O registro de verdade é independente do diagnóstico quanto ao fluxo de dados, mas ambas as partes executam no mesmo processo de simulação e ainda não constituem validação externa ou referência experimental independente. A análise comparativa com métricas de acerto por classe fica para uma etapa posterior.

### Reverificação dos quadros arquivados

Após gerar uma nova execução com `run_scenarios.py`, verifique o SHA-256
diretamente dos bytes preservados em `input_frames.json`:

```bash
python run_scenarios.py --run-id s01-byte-audit-001
python verify_evidence.py run-artifacts/s01-byte-audit-001
python replay_observations.py run-artifacts/s01-byte-audit-001
python evaluate_scenarios.py run-artifacts/s01-byte-audit-001
```

O verificador é implementado separadamente do gerador e não utiliza o codec,
o monitor de sequência nem a função de hash da geração. Reconstrói quadros
binários de 12 bytes a partir do hexadecimal, concatena `uint32_be(tamanho)`
e os bytes de cada quadro na ordem original e calcula SHA-256. Compara o
resultado com os hashes em `observations.json` e `ground_truth.json`,
validando também número de quadros e identificadores.

O resultado fica em `evidence_verification.json` e não sobrescreve versões
anteriores. Os testes cobrem alteração de bit, troca de ordem, falta de
quadro, hexadecimal inválido e alteração isolada de hashes.

**Limite de proveniência:** os quadros arquivados representam os dados
pós-intervenção recebidos pelo simulador. Quadros omitidos não aparecem
nesse arquivo. Recomputar o hash confirma a consistência dos registros,
não autentica sua origem nem impede adulteração conjunta de dados e hashes.

### Reprodução dos eventos a partir dos quadros armazenados

O comando abaixo executa uma **nova passagem pelo mesmo decoder** e pelo
`SequenceTracker` sobre os bytes preservados em `input_frames.json`,
sem consultar o gabarito das intervenções e sem reutilizar a função
`build_report()` que produziu as observações iniciais.

```bash
python replay_observations.py run-artifacts/s01-byte-audit-001
```

O resultado é salvo em `replay_verification.json`. O script compara
**cada evento** (status, índice, origem, número de sequência e estimativa
de lacuna ou razão de rejeição) e os **contadores recalculados** com
`observations.json`. Inconsistências de hash, identificação ou formato
bloqueiam o replay e geram status `unverifiable`; divergências nos
eventos/contadores resultam em `mismatch`. Quadros reproduzidos com os
mesmos resultados recebem `matched`. Arquivos anteriores não são
sobrescritos.

O replay fornece uma checagem adicional de **reprodutibilidade**: usa
o mesmo algoritmo do receptor e não constitui um decodificador de referência
independente, nem certificação espacial. A observação de lacuna não
comprova perda física. Consulte [VALIDATION.md](VALIDATION.md).

### Validação integrada e execução contínua

O teste `tests/test_integration.py` executa os próprios comandos de geração e avaliação
em diretórios temporários. Valida os cinco cenários reais, verifica hashes cruzados,
proteção contra sobrescrita e a diferenciação entre divergência e inconsistência.
Foi corrigido o caminho da política nos testes do avaliador para apontar ao diretório
raiz deste laboratório.

O workflow de CI do GitHub Actions (`.github/workflows/s01-validation.yml`) executa a
suíte e uma geração/avaliação integrada usando Python 3.13. A configuração prevê
preservação temporária de artefatos por 14 dias; a execução e seu status devem ser
verificados na página Actions antes de tratar o resultado como evidência confirmada.

Veja [Validação integrada reproduzível](VALIDATION.md) para os critérios de aceite,
comandos, proveniência dos resultados e limites da demonstração.

### Avaliação pós-execução e critérios definidos

A política versionada `evaluation_policy.json` registra os resultados esperados para os cinco cenários determinísticos, inclusive contadores, sequência de estados, razão de rejeição de quadro inválido e os detalhes da intervenção conhecida pelo gerador. O avaliador lê separadamente `observations.json` e `ground_truth.json`, sem alterar a classificação feita pelo receptor e sem transmitir o gabarito ao decodificador.

Para gerar uma nova execução e avaliá-la a partir do diretório deste laboratório:

```bash
python run_scenarios.py --run-id s01-evaluation-001
python evaluate_scenarios.py run-artifacts/s01-evaluation-001
python -m unittest discover -s tests -v
```

Escolha outro identificador em execuções futuras. O avaliador não sobrescreve `evaluation.json` e `evaluation_summary.md` quando já existem. Ambos são gravados em `run-artifacts/<run_id>/` e permanecem ignorados pelo Git até revisão explícita.

| Cenário | Recebidos previstos | Inválidos | Lacunas | Duplicados | Fora de ordem |
|---|---:|---:|---:|---:|---:|
| `baseline` | 5 | 0 | 0 | 0 | 0 |
| `drop` | 4 | 0 | 1 | 0 | 0 |
| `duplicate` | 6 | 0 | 0 | 1 | 0 |
| `reorder` | 5 | 0 | 1 | 0 | 1 |
| `corrupt` | 5 | 1 | 1 | 0 | 0 |

**Vereditos:** `conformant` significa que os relatórios são consistentes e obedecem às expectativas; `deviation` indica eventos ou contadores divergentes da política; `inconsistent` identifica problemas nos registros, incluindo contagens contraditórias, identificadores, detalhes do gabarito ou hashes incompatíveis. A ferramenta retorna código 0 se todos os cenários forem conformes, 1 em caso de divergência/inconsistência e 2 para erro de leitura ou saída já existente.

**Limitações:** a auditoria externa dos bytes é possível apenas em novas execuções que preservam `input_frames.json`; execuções anteriores não continham esse arquivo. Gerador e receptor têm fluxos de dados distintos, mas compartilham uma única simulação. Não há evidências de enlace RF ou hardware nem classificação cega da causa. A lacuna em `reorder` não implica perda real. Os cinco casos didáticos não permitem estimar sensibilidade, precisão, recall ou acurácia de um classificador.

Foram executados localmente **14 novos testes automatizados (14/14)** com fixtures JSON representativas, incluindo os três vereditos e a prevenção de sobrescrita. A execução integrada dos programas com novos relatórios deve ser reproduzida no ambiente do leitor usando os comandos acima.

## Validação desta iteração

Em ambiente de desenvolvimento com **Python 3.13.5**, foram executados **13 testes automatizados**, com resultado **OK (13/13)**. A execução local de `demo.py` produziu, na ordem, os estados `first`, `in_order`, `gap` (1 quadro estimado), `duplicate`, `out_of_order` e `in_order`, além da rejeição de um quadro corrompido com `CRC mismatch`.

Com o registro JSON, mais **6 testes automatizados** foram adicionados; a suíte conjunta foi executada em Python 3.13.5 e aprovou **19/19 testes**. A geração do relatório e a recusa de sobrescrita também foram verificadas localmente.

Nesta etapa, foram adicionados **12 testes** para os cenários independentes. A suíte completa foi executada localmente em Python 3.13.5: **31 testes aprovados (31/31)**. Também foi executado o comando `run_scenarios.py` com os cinco cenários e verificada a geração dos arquivos, a correspondência dos hashes e a recusa de sobrescrita.

Esses resultados demonstram comportamento do **software de simulação**, não desempenho de telemetria espacial ou de uma transmissão real. O teste deve ser repetido no ambiente de quem reproduzir o laboratório.

## Próximas etapas e critério de conclusão

- [x] Definir um formato binário de teste, versionado e com unidades explícitas.
- [x] Implementar codificação, decodificação e detecção de corrupção por CRC.
- [x] Criar uma demonstração determinística de sequência e falhas.
- [x] Adicionar testes offline para os comportamentos implementados.
- [x] Registrar uma execução sintética de referência em JSON com contadores e SHA-256.
- [x] Formalizar cenários sintéticos independentes com parâmetros, `run_id` e relatórios JSON persistidos localmente.
- [x] Separar gabarito do gerador e observações do receptor, vinculando-os por SHA-256.
- [ ] Revisar e publicar evidências representativas dos ensaios, com proveniência e limitações.
- [x] Implementar teste de integração de geração → observação → avaliação e fluxo CI reexecutável.
- [x] Verificar a execução de CI com 49 testes e cinco cenários conformes (19/11/2026).
- [x] Acrescentar preservação de quadros pós-intervenção e auditoria SHA-256 dos bytes em novas execuções.
- [x] Confirmar e registrar execução de CI da auditoria SHA-256 (19/11/2026, 61 testes aprovados e 5/5 hashes verificados).
- [x] Registrar contagens descritivas e limitações para os cinco cenários sintéticos.
- [x] Publicar política explícita de expectativas e avaliação da conformidade para os cinco cenários de software.
- [x] Implementar replay dos quadros arquivados e comparar eventos e contadores do receptor.
- [x] Confirmar o replay em execução aprovada do GitHub Actions (19/11/2026: 70 testes e 5/5 replays correspondentes).
- [ ] Realizar estudo comparativo com múltiplas replicações e método independente adequado à detecção de causas.
- [ ] Avaliar a integração futura com GSE, observabilidade e injeção controlada de falhas.

O **S01 permanece em desenvolvimento**. A conclusão do laboratório exige resultados e evidências do protocolo experimental completo, não apenas a existência de código e testes unitários.

[Todos os laboratórios](../README.md) · [Método experimental](../../docs/experimental-method.md) · [Arquitetura](../../docs/architecture.md)