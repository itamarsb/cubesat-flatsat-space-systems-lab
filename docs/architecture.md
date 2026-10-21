# Arquitetura de referência — FlatSat, GSE e observabilidade

**Natureza:** arquitetura-alvo, sujeita à validação nos laboratórios.

## Componentes

| Bloco | Responsabilidade |
|:---:|:---:|
| Fonte simulada | Gerar telemetria e cenários de referência controlados |
| FlatSat / subsistema embarcado | Executar firmware, adquirir sinais e produzir pacotes |
| Transporte | Serial/USB na primeira fase; RF conduzida somente após revisão específica |
| GSE | Receber, validar e armazenar quadros e metadados |
| Observabilidade | Expor métricas, eventos, estado dos serviços e painéis |
| Análise | Correlacionar indicadores e avaliar hipóteses de falha |

## Fluxo experimental

~~~mermaid
flowchart LR
    E[Simulador ou firmware embarcado] --> T[Interface serial / USB]
    T --> G[GSE]
    G --> P[Validação e armazenamento]
    P --> O[Observabilidade]
    O --> A[Análise de falhas]
~~~

## Telemetria

Os pacotes experimentais serão versionados e poderão conter:

- identificador de fonte ou subsistema;
- identificador de ensaio;
- contador de sequência;
- timestamp quando houver relógio de referência;
- grandezas de sensores com unidade definida;
- checksum ou CRC para verificação de integridade.

Protocolos como CCSDS, AX.25 e KISS poderão ser estudados em laboratório. Formatos simplificados não serão apresentados como plenamente compatíveis sem ensaios de interoperabilidade.

## Dados públicos de estações terrestres

As observações de pequenos satélites obtidas em fontes públicas constituem uma frente separada dos ensaios com o FlatSat. A coleta deverá registrar a origem, a licença, a janela de observação, a geometria e a qualidade da recepção.

A ausência de pacotes pode ter origem em diferentes pontos da cadeia, inclusive em fatores orbitais, propagação, interferência e indisponibilidade do segmento terrestre.

## Indicadores

| Etapa | Evidências previstas |
|---|---|
| Emissor | Quadros gerados, sequência, reinicializações |
| Transporte | Perdas estimadas, quadros inválidos, atrasos |
| Receptor | Quadros recebidos, erros de validação, disponibilidade |
| Observabilidade | Coleta de métricas, registros, atualização dos painéis |
| Análise | Acertos e erros por classe, abstenções, cobertura de diagnóstico |

A classificação **indeterminada** permanece válida quando faltarem evidências suficientes.

[Roadmap](roadmap.md) · [Método experimental](experimental-method.md)
