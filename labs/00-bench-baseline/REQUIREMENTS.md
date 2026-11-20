# S00 — requisitos e critérios de preparação da bancada

**Estado:** especificação inicial; requisitos propostos, ainda não validados em bancada.  
**Natureza:** planejamento verificável, não relatório de execução.

## Objetivo e limite

Definir os requisitos mínimos de ambiente, instrumentação, alimentação,
interfaces, segurança e rastreabilidade necessários para planejar uma bancada
de telemetria de pequenos satélites. O S00 **não implementa** um FlatSat
físico, um enlace RF ou firmware. A simulação S01 já aceita constitui
referência de formato de pacote, mas não prova compatibilidade elétrica.

A hipótese de trabalho será examinada **depois** da verificação do inventário:
*é possível organizar uma configuração de bancada de baixa tensão, com
interfaces explicitamente identificadas e riscos tratados, que suporte
futuros ensaios de telemetria de modo rastreável e repetível?*

## Matriz inicial de requisitos

| ID | Requisito | Evidência necessária | Estado |
|---|---|---|---|
| S00-R01 | Inventariar apenas equipamentos efetivamente disponíveis e seus modelos | Registro em [INVENTORY.md](INVENTORY.md), com fonte verificável | Pendente |
| S00-R02 | Registrar alimentação nominal, corrente, polaridade, conectores e tolerâncias de cada componente escolhido | Datasheet/manual identificado, conferência de bancada | Pendente |
| S00-R03 | Definir os limites do ambiente de teste e interfaces entre computador, alvo e fonte | Matriz em [INTERFACES.md](INTERFACES.md) revisada | Pendente |
| S00-R04 | Determinar esquema de aterramento e referência comum **somente quando exigido pelo circuito** | Diagrama elétrico revisado e compatibilidade comprovada | Pendente |
| S00-R05 | Identificar pontos de medição, instrumentação disponível e método de registro | Instrumento identificado, faixa e procedimento documentados | Pendente |
| S00-R06 | Analisar riscos de alimentação, ESD, curtos, inversão de polaridade e conexões | [RISK-REGISTER.md](RISK-REGISTER.md) revisado e controles aplicáveis | Pendente |
| S00-R07 | Definir caso de aceitação seguro para a futura bancada, com critérios de interrupção | Procedimento de ensaio, inspeção e registro de resultado | Pendente |
| S00-R08 | Garantir rastreabilidade das decisões, mudanças e evidências | Revisão do código/documentos, identificação e histórico das verificações | Pendente |

A matriz acima é uma **proposta**, não comprova que os requisitos foram
executados ou aceitos. A validação será registrada por data, equipamento,
responsável técnico pelo ensaio e evidência correspondente.

## Condições para passar de planejamento a ensaio

1. Confirmar quais equipamentos e componentes estão realmente disponíveis.
2. Obter os valores de tensão, corrente e limites elétricos nas fontes
   primárias dos componentes selecionados.
3. Revisar a topologia, a proteção elétrica, as interfaces e os riscos
   antes de interligar ou energizar componentes.
4. Definir procedimento específico de ensaio, critérios de parada e forma
   de captura dos dados.
5. Registrar configuração e resultados, distinguindo claramente
   medidas físicas de dados sintéticos.

## Critérios de conclusão do S00

O S00 poderá ser avaliado para encerramento somente quando o inventário
estiver verificado, as conexões escolhidas estiverem documentadas e
revisadas, os riscos relevantes estiverem tratados e houver evidências
de uma configuração mínima efetivamente inspecionada. Publicar estes
documentos **não satisfaz** esse conjunto de critérios.

### Exclusões

Sem testes de radiofrequência nesta fase. Enlace conduzido será tratado
em S07 após revisão de segurança e exigências aplicáveis; firmware e sensores
pertencem ao S02, GSE ao S03 e observabilidade ao S04.

[Visão geral S00](README.md) · [Método experimental](../../docs/experimental-method.md) · [Roadmap](../../docs/roadmap.md)
