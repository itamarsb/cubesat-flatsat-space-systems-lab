# S01 — Simulação e integridade da telemetria

**Situação:** Em desenvolvimento — primeira iteração de software implementada e testada.

## Objetivo

Gerar quadros sintéticos de telemetria, validar sua integridade e analisar o comportamento de um receptor diante de sequências normais, perdas estimadas, duplicações, reordenação e corrupção de dados.

Esta primeira iteração é **exclusivamente uma simulação local em Python**. Não utiliza hardware, canal de rádio, estação terrestre ou dados orbitais reais. O formato binário é didático e **não declara conformidade com CCSDS, AX.25 ou outros protocolos espaciais**.

## Implementação disponível

| Arquivo | Finalidade |
|---|---|
| `packet.py` | Codificador e decodificador de quadros, CRC-16 e observação de sequência por fonte |
| `demo.py` | Demonstração determinística de recepção, lacuna, duplicação, reordenação e corrupção |
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

## Validação desta iteração

Em ambiente de desenvolvimento com **Python 3.13.5**, foram executados **13 testes automatizados**, com resultado **OK (13/13)**. A execução local de `demo.py` produziu, na ordem, os estados `first`, `in_order`, `gap` (1 quadro estimado), `duplicate`, `out_of_order` e `in_order`, além da rejeição de um quadro corrompido com `CRC mismatch`.

Esses resultados demonstram comportamento do **software de simulação**, não desempenho de telemetria espacial ou de uma transmissão real. O teste deve ser repetido no ambiente de quem reproduzir o laboratório.

## Próximas etapas e critério de conclusão

- [x] Definir um formato binário de teste, versionado e com unidades explícitas.
- [x] Implementar codificação, decodificação e detecção de corrupção por CRC.
- [x] Criar uma demonstração determinística de sequência e falhas.
- [x] Adicionar testes offline para os comportamentos implementados.
- [ ] Formalizar cenários experimentais com parâmetros, `run_id`, logs persistidos e evidências de execução.
- [ ] Medir resultados por cenário e documentar limitações observadas.
- [ ] Avaliar a integração futura com GSE, observabilidade e injeção controlada de falhas.

O **S01 permanece em desenvolvimento**. A conclusão do laboratório exige resultados e evidências do protocolo experimental completo, não apenas a existência de código e testes unitários.

[Todos os laboratórios](../README.md) · [Método experimental](../../docs/experimental-method.md) · [Arquitetura](../../docs/architecture.md)