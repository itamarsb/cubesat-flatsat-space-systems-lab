# CubeSat & FlatSat Space Systems Lab

**CubeSats · Nanosatélites · FlatSat · Sistemas Embarcados · Telemetria · Segmento Terrestre · Observabilidade**

[English](README.en.md) · [Laboratórios](labs/README.md) · [Roadmap](docs/roadmap.md) · [Arquitetura](docs/architecture.md) · [Método experimental](docs/experimental-method.md)

## Visão geral

O **CubeSat & FlatSat Space Systems Lab** é um laboratório de engenharia dedicado ao estudo e à implementação de subsistemas experimentais para pequenos satélites. Seu desenvolvimento integra hardware de bancada, firmware, aquisição de sensores, protocolos de telemetria, aplicações de segmento terrestre e práticas de observabilidade e confiabilidade.

O projeto utiliza um **FlatSat** — montagem de subsistemas eletrônicos interligados em bancada — para reproduzir e investigar funções típicas de um pequeno satélite, sem alegar qualificação para voo ou equivalência com uma missão orbital. A evolução do laboratório parte da simulação e avança gradualmente para hardware físico e testes de comunicação.

**Situação:** a trilha espacial está em preparação. As etapas indicadas como planejadas ainda não possuem resultados experimentais validados neste repositório.

## Áreas de desenvolvimento

| Área | Aplicações no laboratório |
|---|---|
| **CubeSat e nanosatélites** | Arquitetura de subsistemas, interfaces, requisitos e integração de protótipos |
| **FlatSat e sistemas embarcados** | Microcontroladores STM32/ESP32, firmware, barramentos, sensores e aquisição de dados |
| **Telemetria e comunicações** | Formatos de pacotes, sequência, integridade, perdas, latência e enlaces experimentais |
| **Segmento terrestre (GSE)** | Recepção, decodificação experimental, armazenamento, interfaces e automação |
| **Observabilidade e confiabilidade** | Métricas, logs, painéis, alertas, análise de incidentes e injeção controlada de falhas |
| **Dados de satélites** | Estudo de observações públicas e condições de recepção, com proveniência documentada |

## Laboratórios

| Lab | Tema | Estado |
|---|---|---|
| [S00](labs/00-bench-baseline/README.md) | Requisitos, instrumentos e arquitetura da bancada | Planejado |
| [S01](labs/01-telemetry-simulation/README.md) | Simulação e integridade de pacotes de telemetria | Planejado |
| [S02](labs/02-embedded-flatsat/README.md) | FlatSat com microcontrolador e aquisição de sensores | Planejado |
| [S03](labs/03-ground-segment/README.md) | Ground Support Equipment (GSE) e recepção | Planejado |
| [S04](labs/04-observability/README.md) | Métricas, logs, painéis e monitoramento | Planejado |
| [S05](labs/05-fault-injection/README.md) | Injeção controlada e análise de falhas | Planejado |
| [S06](labs/06-public-observations/README.md) | Observações públicas de pequenos satélites | Planejado |
| [S07](labs/07-conducted-rf/README.md) | Enlace de RF conduzido e medições | Condicionado a análise técnica e regulatória |
| [S08](labs/08-nonflight-1u/README.md) | Integração elétrica e mecânica de um protótipo 1U de bancada | Estudo de viabilidade |

O [roadmap](docs/roadmap.md) define a sequência de implementação, as dependências e os critérios de conclusão. Conhecimentos de eletrônica e aviônica permanecem associados ao projeto como base técnica, descrita em [Fundamentos de sistemas embarcados](docs/embedded-avionics-foundations.md).

## Arquitetura experimental

~~~mermaid
flowchart LR
    S[Simulador / FlatSat] --> C[Serial / USB]
    C --> G[GSE: recepção e validação]
    G --> D[(Registros e dados)]
    G --> M[Métricas e eventos]
    M --> O[Prometheus / Grafana]
    D --> A[Análise de falhas]
    O --> A
    P[Observações públicas de satélites] --> V[Proveniência / geometria / qualidade]
    V --> A
~~~

O fluxo representa uma **arquitetura-alvo**. Os testes físicos e a integração da plataforma serão documentados por laboratório, com a distinção entre dados simulados, dados de bancada e observações externas.

[Arquitetura detalhada](docs/architecture.md)

## Método de engenharia

Cada laboratório registra os requisitos de execução, materiais, configurações, procedimentos, critérios de aceite, testes e evidências. Os estados de desenvolvimento são mantidos no README correspondente, diferenciando planejamento, execução em andamento e validação concluída.

Para ensaios de diagnóstico, a causa de falhas introduzidas em bancada é registrada separadamente da análise produzida pelo sistema. Observações públicas sem recepção não são tratadas automaticamente como prova de falha do satélite.

[Método experimental e evidências](docs/experimental-method.md)

## Segurança e limites

O laboratório destina-se ao desenvolvimento e à pesquisa **em bancada**. Seus protótipos não são equipamentos certificados para operação espacial, aeronáutica ou de segurança crítica.

A etapa inicial utiliza simulação e comunicação serial/USB. Ensaios com radiofrequência somente serão realizados após avaliação de atenuação, impedância, potência, isolamento, proteção dos receptores e requisitos regulatórios aplicáveis. A utilização de enlace conduzido não dispensa essa verificação.

[Critérios de segurança e radiofrequência](docs/rf-safety.md)

## Projetos relacionados

- [Observability Engineering Framework](https://github.com/itamarsb/Observability-Engineering-Framework) — instrumentação e avaliação de observabilidade.
- [Hybrid Observability Platform](https://github.com/itamarsb/hybrid-observability-platform) — telemetria de aplicações, métricas, logs e traces.
- [LiDAR/Sonar Lab](https://github.com/itamarsb/lidar-sonar-lab) — aquisição de sensores e monitoramento experimental.

---

**Autor:** Itamar de Sá Britto Júnior · Engenharia de Computação · Sistemas Embarcados · Telemetria · Observabilidade

---

## 📈 Repository Metrics

<p align="center">

<a href="http://s05.flagcounter.com/more/CR0"><img src="https://s05.flagcounter.com/map/CR0/size_l/txt_000000/border_CCCCCC/pageviews_1/viewers_0/flags_0/" alt="Flag Counter" border="0"></a>

</p>
