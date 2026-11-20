# S00 — inventário de bancada a verificar

**Estado:** modelo inicial sem levantamento realizado.  
**Regra de rastreabilidade:** nenhum item abaixo constitui declaração de posse, disponibilidade ou medição.

## Registro de equipamentos reais

Preencher **somente após inspeção**. Uma linha por equipamento físico
identificado; não atribuir número de série, disponibilidade, condições
elétricas ou resultados a itens não conferidos.

| ID | Categoria | Fabricante/modelo | Disponibilidade verificada | Alimentação/faixa nominal | Interface | Evidência / fonte | Data |
|---|---|---|---|---|---|---|---|
| — | A levantar | Não informado | Não verificada | Não verificada | Não verificada | Pendente | — |

**Orientação de preenchimento:** dados de placa, manual ou datasheet
identificados devem ser distinguidos de medições feitas na bancada. Uma
ficha técnica descreve especificações do fabricante; não demonstra que
uma unidade específica foi medida ou que opera corretamente.

## Categorias candidatas à avaliação

As categorias abaixo são uma **lista de verificação de necessidades**,
não uma lista de equipamentos existentes:

| Categoria | Função prevista | Situação |
|---|---|---|
| Computador de desenvolvimento | Executar código, registrar e analisar ensaios | Disponibilidade e configuração a confirmar |
| Plataforma embarcada (se adotada) | Gerar pacotes em hardware em etapa futura | Modelo e disponibilidade a definir |
| Fonte de bancada com proteção | Alimentação controlada de componentes | Necessidade, modelo e limites a definir |
| Multímetro | Conferência de tensão, continuidade e polaridade | Disponibilidade e faixa a confirmar |
| Analisador lógico (opcional) | Investigar comunicação digital | Necessidade a avaliar |
| Osciloscópio (opcional) | Observar sinais e transientes | Necessidade e disponibilidade a avaliar |
| Cabos, conectores e proteção | Conexões e mitigação de risco | Especificação e inspeção pendentes |

Não conectar dispositivos com base nesta tabela. Esquemas, tensões, pinagens
e método de proteção dependem de componentes **efetivamente selecionados**.

## Protocolo de conferência

1. Identificar o item por fabricante e modelo exatos e registrar a origem.
2. Conferir visualmente integridade, conectores e identificação elétrica,
   sem energizá-lo antes da revisão pertinente.
3. Identificar manual/datasheet e anotar os limites pertinentes.
4. Associar o item à interface e ao risco correspondentes.
5. Registrar data e evidência da conferência; manter
   `Não verificada` se não houve inspeção efetiva.

[Requisitos](REQUIREMENTS.md) · [Interfaces](INTERFACES.md) · [Riscos](RISK-REGISTER.md)
