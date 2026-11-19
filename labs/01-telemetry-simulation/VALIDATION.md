# S01 — validação integrada reproduzível

## Escopo

O S01 contém um gerador determinístico de quadros sintéticos, um receptor que
interpreta CRC e sequência, um gabarito do gerador separado das observações
e uma política de avaliação de conformidade. Este procedimento verifica apenas
o comportamento do **software**, sem testar RF, GSE ou hardware espacial.

## Execução local

Execute a partir de `labs/01-telemetry-simulation`:

```bash
python -m unittest discover -s tests -v
python run_scenarios.py --run-id s01-local-verification
python verify_evidence.py run-artifacts/s01-local-verification
python replay_observations.py run-artifacts/s01-local-verification
python evaluate_scenarios.py run-artifacts/s01-local-verification
```

Escolha um identificador diferente a cada nova execução. Não reexecute a
avaliação no mesmo diretório: as saídas anteriores são preservadas e uma nova
tentativa é recusada. Os testes de integração usam diretórios temporários e
não deixam artefatos no repositório.

A avaliação gera `evaluation.json` e `evaluation_summary.md` em
`run-artifacts/<run_id>/`, além dos pares `observations.json` e
`ground_truth.json` e do arquivo `input_frames.json` de cada cenário.
O verificador cria `evidence_verification.json`, que contém o SHA-256
recomputado a partir dos quadros em hexadecimal, antes da comparação com os hashes
declarados nos dois relatórios. Revise todos os registros antes de
publicar qualquer artefato. Essa pasta é ignorada pelo Git.

## Validação contínua e preservação

O workflow `.github/workflows/s01-validation.yml` executa a suíte offline
e os cinco cenários em Python 3.13 para alterações do S01. Após uma execução
bem-sucedida, a página **Actions** do GitHub registra o commit e o status.
Um artefato de execução de nome `s01-validation-<run_id>` contém os JSONs e
o resumo Markdown, com retenção configurada em 14 dias. A disponibilidade
depende da execução efetiva e das permissões do GitHub Actions.

Para citar um resultado, registre o link da execução no Actions, o commit
exato, o nome do artefato, as versões do ambiente e os hashes dos dados.
Não descreva como verificação concluída uma execução ainda não observada.
Não versionamos automaticamente os arquivos de `run-artifacts/`.

## Evidência efetivamente observada — 19/11/2026

- **Execução GitHub Actions:** [S01 Offline Telemetry Validation #44606673467](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44606673467)
- **Código testado:** commit `d4fdb35ec9dbd396c05b36ec491cdf53ccb7b54c` (`main`).
- **Ambiente do job:** Ubuntu hospedado pelo GitHub, Python 3.13.
- **Teste automatizado:** **49 testes executados, todos com resultado OK**, segundo os logs do job.
- **Integração de ponta a ponta:** `run_scenarios.py` seguido de `evaluate_scenarios.py`; **5 cenários conformes, 0 divergentes e 0 inconsistentes**, conforme as verificações do job.
- **Artefato:** [s01-validation-44606673467](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44606673467/artifacts/14570049126), ID `14570049126`; retenção prevista até **2026-12-03 20:14:57 UTC** (14 dias), sujeita à política do GitHub.
- **Limite:** a aprovação verifica somente a conformidade dos cinco cenários sintéticos. Não constitui evidência de desempenho de RF, robustez do FlatSat físico ou capacidade de identificar causas reais de falhas.

O primeiro job apresentou um aviso de depreciação do runtime Node.js 20 nas ações auxiliares de CI, **sem falha na execução**. O workflow foi posteriormente atualizado para versões das ações compatíveis com Node.js 24. Sua nova execução deve ser conferida separadamente.

## Reprodutibilidade dos quadros e limites de proveniência

O arquivo `input_frames.json` preserva, para cada cenário, os bytes exatos
apresentados ao receptor **depois** da intervenção (formato hexadecimal,
ordem e índice do quadro). A auditoria independente implementada em
`verify_evidence.py` utiliza somente bibliotecas padrão e não chama a
função `sha256_frames` do gerador. Recalcula o hash pela convenção
`SHA256(concat(uint32_be(length(frame)), frame))` para todos os quadros
na ordem de recepção.

Um quadro omitido antes de ser entregue ao receptor não estará no arquivo
de entradas. Dados e hashes alterados em conjunto podem passar na auditoria:
o processo não fornece autenticação, imutabilidade criptográfica da origem
ou validação de telemetria espacial. O verificador também não reexecuta
a classificação dos eventos do receptor, tarefa tratada pelos testes e
pela avaliação separados.

## Evidência auditada — quadros originais da simulação (19/11/2026)

- **Workflow efetivamente concluído:** [execução #44625657432](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44625657432), `success`.
- **Commit executado:** `d76c30eb53ffa3a099fba2bb583729f8d588582a` (branch `main`).
- **Resultados da suíte:** 61 testes `unittest`, todos aprovados.
- **Avaliação funcional:** cinco cenários conformes, zero divergentes, zero inconsistentes.
- **Auditoria dos bytes:** cinco arquivos de quadros reconstruídos e verificados, sem erros.
- **Artefato:** [s01-validation-44625657432](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44625657432/artifacts/14577398750), ID `14577398750`; expiração informada pelo GitHub: **03/12/2026, 22:08:22 UTC**.

### Hashes SHA-256 recalculados do artefato baixado

| Cenário | Quadros de entrada do receptor | SHA-256 recalculado |
|---|---:|---|
| `baseline` | 5 | `1afde3c85f9c33fc572abfb530729253779ec42083292d9a2db75b59f1123de2` |
| `drop` | 4 | `343300aff7356dc1b7b6457b67be641944b6145313fb1644735b747bdad80908` |
| `duplicate` | 6 | `d0f17bf6f95c5da85b3b580b5727a631cb1add5448b1cc2d66e50ac122bc5ca6` |
| `reorder` | 5 | `079c3ab16814988d5d9a861d5a3659c7df095ad0fcde816186d4d6ac16be18d9` |
| `corrupt` | 5 | `f79aafc0f5dd0d770240137ce92245606830217c0b609faedf6ff1aaf740fd8a` |

A verificação independente foi repetida a partir do arquivo ZIP baixado da execução acima,
usando a reconstrução de `bytes_hex` e `hashlib.sha256`. Cada resultado coincidiu com
o digest registrado em `observations.json` e `ground_truth.json`.

**SHA-256 da cópia ZIP baixada:** `5779bb7b54bae7278362f2b796dee3b4a6c8ace3448755fd99e7ce0cef680383`.
Esse hash identifica a cópia ZIP examinada; o artefato remoto poderá deixar de estar
disponível após o período de retenção. Os cinco hashes da tabela permanecem como
referências verificáveis para reproduções futuras do experimento.

Esses valores são provas de **consistência entre os arquivos** de uma simulação
determinística e não assinaturas digitais. Eles não certificam dados de sensores,
operação de um enlace espacial, nem inviabilizam adulteração coordenada dos arquivos.

## Replay do receptor a partir dos quadros preservados

O script `replay_observations.py` lê novamente os bytes em
`input_frames.json` e reproduz a decodificação, a verificação CRC e o
acompanhamento da sequência. Compara cada evento e todos os contadores
do replay com `observations.json`. Antes do replay, requer a integridade
dos hashes e dos metadados verificados por `audit_scenario`.

O registro `replay_verification.json` diferencia três situações:

- `matched`: os bytes arquivados reproduziram eventos e contadores;
- `mismatch`: os arquivos estão íntegros, mas as observações divergem;
- `unverifiable`: hash, índices ou metadados de entrada não podem ser validados.

Os testes de regressão simulam alterações em eventos, contadores e
quadros; também alteram bytes e hashes simultaneamente para mostrar
que **conferir apenas hashes declarados não valida a coerência dos
eventos com o fluxo de entrada**.

O replay não utiliza informações de falha do gerador, mas reutiliza o
mesmo decodificador e a mesma classe de sequência da implementação
original. Assim, demonstra reprodutibilidade do software, **não é uma
implementação independente para certificar a exatidão do algoritmo**.
Não há medição física de taxa de perda ou confiabilidade espacial.

## Critérios de aceite

1. A suíte `unittest` passa sem falhas.
2. `run_scenarios.py` produz observações e gabarito para cinco cenários.
3. `evaluate_scenarios.py` termina com código 0 e gera o par de relatórios.
4. `evaluation.json` mostra 5 conformes, 0 divergentes e 0 inconsistentes.
5. Tests automatizados demonstram os vereditos alternativos e recusa de
   sobrescrita sem alterar arquivos preexistentes.
6. Para execuções atuais, o verificador reconstrói bytes de `input_frames.json`
   e recalcula SHA-256, comparando com os dois relatórios de cada cenário.
   A reverificação independente **não se aplica às execuções antigas**, que
   não preservavam esses bytes.
7. O arquivo de auditoria informa **5 cenários verificados, 0 falhas**.
   O hash não é assinatura digital nem autentica a origem dos dados.
8. O replay confirma **5 cenários correspondentes, 0 divergências e 0 não verificáveis**.

A lacuna vista no cenário `reorder` não é uma perda comprovada.
Os cinco cenários não constituem amostra estatística para estimar acurácia,
precisão, recall ou sensibilidade de diagnóstico de falhas.
