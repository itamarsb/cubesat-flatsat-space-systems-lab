# S00 — registro preliminar de riscos de bancada

**Estado:** análise preventiva inicial. Não foram realizadas medições,
inspeções elétricas ou ensaios físicos. Os impactos apresentados são
**qualitativos**, não probabilidades ou resultados instrumentais.

| ID | Risco potencial | Consequência possível | Controle antes da execução | Estado |
|---|---|---|---|---|
| R-01 | Tensão ou polaridade incorreta | Danos a componentes, aquecimento | Conferir datasheets, pinagens, limites e proteções; revisar ligações sem energia | Aberto |
| R-02 | Curto-circuito ou corrente excessiva | Aquecimento e dano à fonte ou circuito | Limitação de corrente adequada, proteção e inspeção prévia | Aberto |
| R-03 | Incompatibilidade entre níveis lógicos | Danos a GPIO e falhas de comunicação | Verificar tolerâncias, referências e necessidade de adaptação de níveis | Aberto |
| R-04 | Descarga eletrostática | Dano latente ou imediato | Controles ESD compatíveis com os componentes selecionados | Aberto |
| R-05 | Conexões e cabos sem identificação | Inversão de sinais, diagnóstico incorreto | Diagrama e rotulagem verificáveis; dupla checagem antes de energizar | Aberto |
| R-06 | Instrumentação inadequada ou mal configurada | Leitura errada, dano ao instrumento | Conferir categoria, faixa, ponta, aterramento e procedimento do instrumento | Aberto |
| R-07 | Confusão entre dados simulados e físicos | Conclusões técnicas indevidas | Identificar `data_origin` e manter evidências e contexto de cada ensaio | Aberto |
| R-08 | Divulgação indevida de evidências | Exposição de credenciais, dados pessoais ou registros não revisados | Inspeção antes de qualquer commit ou publicação | Aberto |

## Critérios de interrupção

Não iniciar ou interromper a preparação para energização se faltarem
informações sobre tensão, corrente, polaridade, proteções, pinagem,
compatibilidade elétrica ou integridade de componentes. Qualquer
aquecimento inesperado, odor, ruído anormal ou indício de curto requer
desenergização segura e investigação antes de novo teste.

Não são previstos ensaios com rede elétrica aberta, altas tensões,
transmissão RF ou condições que excedam a infraestrutura e a formação
disponíveis. RF conduzida e ensaios espaciais são temas separados,
dependentes de revisão técnica e regulatória.

## Revisão e encerramento

Este registro deverá ser atualizado depois da escolha de equipamentos,
com probabilidade/impacto e risco residual **apenas quando houver base
para avaliá-los**. Um risco será encerrado somente com medida de controle
verificada e evidência. A publicação desta lista não encerra nenhum risco.

[Requisitos](REQUIREMENTS.md) · [Interfaces](INTERFACES.md) · [Inventário](INVENTORY.md)
