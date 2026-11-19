# S01 — evidência de referência v1 (simulação sintética)

Esta pasta preserva uma cópia **inalterada** do ZIP produzido pelo GitHub Actions
para o experimento S01 em **19/11/2026**, juntamente com um manifesto dos
**19 arquivos originais** dentro do ZIP.

- **Execução de origem:** [GitHub Actions #44628209124](https://github.com/itamarsb/cubesat-flatsat-space-systems-lab/actions/runs/44628209124).
- **Commit de origem:** `ac233f6ad9d227ef22c1b144350c1659722c9767`.
- **Artefato original:** `s01-validation-44628209124` (ID `14581060691`).
- **Identificação da execução:** `s01-ci-reference`, Python 3.13.18, Linux.
- **Arquivo preservado:** `s01-reference-2026-11-19.zip`, 12.375 bytes.
- **SHA-256 do ZIP:** `11986c730e4e9102b930dbbdca42fa4a04c36515204fc08f0830e73cdf3be47c`.

## Conteúdo e origem

O ZIP contém `input_frames.json`, `observations.json` e
`ground_truth.json` de cada cenário: `baseline`, `drop`,
`duplicate`, `reorder`, `corrupt`. Contém também quatro arquivos de
avaliação: `evaluation.json`, `evaluation_summary.md`,
`evidence_verification.json` e `replay_verification.json`.

O `manifest.json` registra, para cada um dos 19 arquivos internos, o
nome, tamanho em bytes e SHA-256. Todos os quadros preservados são dados
**sintéticos e pós-intervenção**, sem captura de enlace físico.
Os dados originais não foram editados ou regenerados na publicação.

## Conferência independente dos arquivos

Na pasta `labs/01-telemetry-simulation`, execute:

```bash
python verify_reference_snapshot.py
```

O verificador usa exclusivamente a biblioteca padrão. Confere o hash
do ZIP, o manifesto, o tamanho e SHA-256 de cada arquivo interno e o SHA-256
dos quadros reconstruídos do hexadecimal, com 4 bytes big-endian de tamanho
prefixando cada quadro. Também verifica identificadores e contadores dos
relatórios de avaliação.

Para reproduzir os eventos e os contadores do receptor com o software
correspondente ao ensaio, consulte o commit de origem e o procedimento
em [VALIDATION.md](../../VALIDATION.md). O verificador do manifesto
não substitui o replay nem a política de avaliação.

**Limites:** um SHA-256 sem assinatura não garante autenticidade; a
reprodução usa o mesmo decodificador do receptor original; os cinco
cenários não são uma amostra estatística de falhas espaciais. O
arquivamento no Git não prova permanência absoluta e depende da
disponibilidade do repositório.
