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
python evaluate_scenarios.py run-artifacts/s01-local-verification
```

Escolha um identificador diferente a cada nova execução. Não reexecute a
avaliação no mesmo diretório: as saídas anteriores são preservadas e uma nova
tentativa é recusada. Os testes de integração usam diretórios temporários e
não deixam artefatos no repositório.

A avaliação gera `evaluation.json` e `evaluation_summary.md` em
`run-artifacts/<run_id>/`, além dos pares `observations.json` e
`ground_truth.json` de cada cenário. Revise todos os registros antes de
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

## Critérios de aceite

1. A suíte `unittest` passa sem falhas.
2. `run_scenarios.py` produz observações e gabarito para cinco cenários.
3. `evaluate_scenarios.py` termina com código 0 e gera o par de relatórios.
4. `evaluation.json` mostra 5 conformes, 0 divergentes e 0 inconsistentes.
5. Tests automatizados demonstram os vereditos alternativos e recusa de
   sobrescrita sem alterar arquivos preexistentes.
6. Os hashes dos relatórios correspondem entre si; **não equivalem à
   revalidação independente dos bytes**, que não são arquivados.

A lacuna vista no cenário `reorder` não é uma perda comprovada.
Os cinco cenários não constituem amostra estatística para estimar acurácia,
precisão, recall ou sensibilidade de diagnóstico de falhas.
