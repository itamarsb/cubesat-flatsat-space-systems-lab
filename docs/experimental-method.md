# Método experimental e evidências

## Objetivo

Registrar configurações, procedimentos e resultados de forma que os experimentos possam ser verificados e reproduzidos.

## Informações mínimas por laboratório

| Elemento | Registro |
|---|---|
| Objetivo e hipótese | Questão técnica e comportamento esperado |
| Topologia | Componentes, interfaces e diagrama |
| Ambiente | Hardware real, firmware, versões, software e dependências |
| Entradas | Origem dos dados, parâmetros, unidades e sementes de simulação |
| Procedimento | Passos da execução e condições iniciais |
| Critérios de aceite | Verificações objetivas antes do ensaio |
| Evidências | Logs, medições, testes, capturas e hashes quando pertinentes |
| Resultados | Valores observados, desvio da referência, falhas e limitações |
| Finalização | Estado final, limpeza e próximos testes |

## Identificação das execuções

Os ensaios serão organizados por identificador **run_id**, associado ao **lab_id**, **scenario_id** e à revisão do código. Sempre que a medição exigir correlação temporal, o relógio utilizado será indicado.

Campos recomendados: **utc_start**, **utc_end**, **data_origin** (*synthetic*, *bench* ou *public*), **git_commit**, **firmware_version**, **params**, **measurements**, **evidence** e **checksums**.

## Experimentos de falha

A falha introduzida na bancada deve ter ponto, instante, duração e causa registrados em uma trilha independente. O resultado calculado pelo sistema de diagnóstico não pode utilizar o próprio gabarito como entrada.

A apresentação dos resultados deverá conter contagens por cenário, indicadores e limites estatísticos adequados à unidade experimental. Em comparações, as regras dos métodos de referência deverão ser descritas antes do ensaio.

## Origem e qualidade dos dados

Simulações, medições de bancada e dados públicos de observação de satélites têm condições de geração distintas e deverão permanecer identificados. Dados externos exigem fonte, período de coleta e observância das permissões de uso e redistribuição.

## Segurança

Ensaios com hardware seguem as especificações elétricas dos componentes. RF depende da [avaliação técnica e regulatória](rf-safety.md). Registros públicos não devem conter credenciais, tokens ou dados pessoais desnecessários.
