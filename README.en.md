# CubeSat & FlatSat Space Systems Lab

**CubeSats · Nanosatellites · FlatSat · Embedded Systems · Telemetry · Ground Segment · Observability**

[Português](README.md) · [Laboratories](labs/README.md) · [Roadmap](docs/roadmap.md) · [Architecture](docs/architecture.md) · [Experimental method](docs/experimental-method.md)

## Overview

The **CubeSat & FlatSat Space Systems Lab** is an engineering laboratory focused on the study and experimental development of small-satellite subsystems. The work connects bench electronics, firmware, sensors, telemetry protocols, ground-support software, observability and reliability engineering.

A **FlatSat** provides a bench-top arrangement of interconnected subsystems for testing functions commonly found in small satellites. This is a non-flight experimental platform, not a flight-qualified spacecraft or an operational orbital mission.

**Current status:** laboratory planning and preparation. Experimental results will be documented after implementation and verification.

## Technical scope

| Area | Laboratory scope |
|:---:|:---:|
| Small-satellite systems | CubeSat/nanosatellite subsystem architecture and prototype integration |
| Embedded engineering | STM32/ESP32, sensors, firmware, interfaces and electrical measurements |
| Telemetry | Packet formats, sequence numbers, error detection, losses and latency |
| Ground segment | Ground Support Equipment (GSE), ingestion, experimental decoding and data storage |
| Observability | Metrics, logs, dashboards, monitoring and controlled fault analysis |
| Public satellite data | Ground-station observation data, reception geometry and provenance |

## Laboratory roadmap

| Lab | Topic | Status |
|---|---|---|
| [S00](labs/00-bench-baseline/README.md) | Bench requirements and inventory | Planned |
| [S01](labs/01-telemetry-simulation/README.md) | Telemetry simulation and packet integrity | Planned |
| [S02](labs/02-embedded-flatsat/README.md) | Embedded FlatSat and sensors | Planned |
| [S03](labs/03-ground-segment/README.md) | Ground Support Equipment | Planned |
| [S04](labs/04-observability/README.md) | Observability pipeline | Planned |
| [S05](labs/05-fault-injection/README.md) | Controlled fault injection | Planned |
| [S06](labs/06-public-observations/README.md) | Public ground-station observations | Planned |
| [S07](labs/07-conducted-rf/README.md) | Conducted RF experiments | Subject to technical/regulatory review |
| [S08](labs/08-nonflight-1u/README.md) | Non-flight 1U bench demonstrator | Feasibility study |

The planned workflow is **simulation → serial/USB FlatSat → telemetry reception and observability → controlled fault analysis → public observation studies**, with RF conducted testing and mechanical integration reserved for later phases.

## Evidence and reliability

Each laboratory documents its configuration, acceptance criteria, procedure, tests, measurements and limitations. Synthetic data, hardware-bench data and public satellite observations remain clearly identified and are not presented interchangeably.

Fault attribution experiments use an independently recorded fault-injection label where available. Missing public telemetry, by itself, does not establish a spacecraft failure.

See the [architecture](docs/architecture.md), [experimental method](docs/experimental-method.md) and [safety requirements](docs/rf-safety.md).

**Author:** Itamar de Sá Britto Júnior · Computer Engineering · Embedded Systems · Space Telemetry · Observability
