# Roadmap — CubeSat, FlatSat e sistemas espaciais de bancada

**Estado geral:** planejamento dos laboratórios. A execução e os resultados serão acrescentados às páginas de cada laboratório.

## Progressão

| Lab | Tema | Entregável de referência | Status |
|---|---|---|---|
| S00 | Baseline de bancada | Diagrama, inventário, interfaces, riscos, critérios de aceite | Planejado |
| S01 | Simulação de telemetria | Pacotes com versão e sequência, verificação de integridade, testes determinísticos | Planejado |
| S02 | FlatSat embarcado | Firmware STM32/ESP32, leituras de sensores, captura serial, comparação com referência | Planejado |
| S03 | Ground Support Equipment | Receptor, validação de quadros, armazenamento e rastreabilidade | Planejado |
| S04 | Observabilidade | Métricas, logs, painéis e validação de disponibilidade da cadeia | Planejado |
| S05 | Injeção de falhas | Cenários de perda, reinício, falha de recepção e gabarito independente | Planejado |
| S06 | Observações públicas | Consulta documentada, geometria, qualidade, origem e limitações de dados | Planejado |
| S07 | RF conduzida | Medições de enlace com condições de potência e segurança verificadas | Condicional |
| S08 | Modelo não espacial 1U | Integração mecânica e elétrica, lista de materiais e ensaios de bancada | Viabilidade |

## Fases

**Fase I — Base experimental (S00–S01):** especificar sinais, interfaces, ambiente de teste e pacotes de telemetria. Definir casos válidos, perdas, quadros inválidos e cenários reprodutíveis.

**Fase II — Hardware e segmento terrestre (S02–S03):** usar microcontrolador e interface serial/USB para produzir quadros observáveis por um receptor/GSE com logs de integridade.

**Fase III — Monitoramento e confiabilidade (S04–S05):** relacionar a recepção de telemetria a indicadores operacionais; aplicar falhas de origem conhecida e comparar diagnóstico com registro independente.

**Fase IV — Observações espaciais (S06):** explorar dados públicos de observações de satélites, observando contexto orbital, condições da recepção e a qualidade da informação disponível.

**Fase V — Ampliação (S07–S08):** examinar enlace de RF conduzido e montagem física de modelo 1U, conforme orçamento, segurança, instrumentos e requisitos legais.

As fases não representam datas de conclusão. Novas etapas poderão ser incorporadas conforme a maturidade do laboratório.

## Critérios de conclusão

- **Planejado:** objetivo, recursos e ensaios previstos.
- **Em andamento:** implementação iniciada; resultados ainda incompletos.
- **Concluído:** critérios de aceite atendidos, evidências e verificações documentadas.
- **Em revisão:** testes identificaram desvios ou pendências de validação.
- **Condicional:** depende de revisão técnica, viabilidade financeira ou requisitos de segurança.

Nenhuma etapa passa a concluída apenas pela existência de código ou documentação. O laboratório deverá apresentar resultados efetivos e as condições em que foram obtidos.

## Fundamentos complementares

O projeto empregará conteúdos de eletrônica, instrumentação, C/C++, STM32/ESP32, UART, SPI, I2C, sistemas de tempo real, tolerância a falhas, modelagem de requisitos e verificação. A progressão desses tópicos está descrita em [fundamentos de sistemas embarcados](embedded-avionics-foundations.md).

## Protocolos e interoperabilidade

Formatos de pacotes inicialmente simplificados poderão servir aos testes didáticos. O estudo de CCSDS, AX.25 e KISS será identificado por versão e escopo. Qualquer alegação de interoperabilidade deverá ser acompanhada de testes com implementações compatíveis; a inspiração em um protocolo não equivale à sua conformidade integral.

## Atribuição de falhas

A análise diferenciará, sempre que possível, emissor de bancada, transporte, GSE e processamento de observabilidade. O experimento deverá registrar as falhas introduzidas separadamente da saída do diagnóstico, além de reportar casos sem informação suficiente.

Dados públicos de satélites reais serão interpretados com cautela, pois uma observação sem telemetria pode ter diversas causas, inclusive geometria e indisponibilidade da estação.

[Arquitetura](architecture.md) · [Método experimental](experimental-method.md) · [Segurança de RF](rf-safety.md)
