# Projeto de Engenharia de Dados

Pipeline de dados de uma empresa de assinaturas (dados fictícios). Limpa e organiza 5 tabelas (clientes, assinaturas, planos, pagamentos e interações) em camadas e entrega 7 tabelas resumidas, prontas para alimentar um dashboard no Google Planilhas.

## Arquitetura

```
Bronze (original) -> Staging (em preparo) -> Silver (limpo e conferido) -> Gold (resumos para o dashboard)
  data/Bronze        notebooks 01 a 05          notebook 06                   notebook 07
```

## Estrutura de pastas

| Pasta / Arquivo | O que tem |
|---|---|
| `data/Bronze/` | Dados originais (nunca editar) |
| `data/Staging/` | Dados em preparo, saída dos notebooks 01 a 05 |
| `data/Silver/` | Dados limpos e aprovados, saída do notebook 06 |
| `data/Gold/` | 7 tabelas resumidas para o dashboard, saída do notebook 07 |
| `notebooks/` | Passo a passo do tratamento |
| `src/` | Funções reutilizáveis (`datas.py`) |
| `tests/` | Testes automáticos das funções do `src/` |
| `dashboard/` | Frontend (`Index.html`) e backend Apps Script (`Code.js`) do dashboard |
| `logs/` | Logs de execução gerados pelo orquestrador (criada automaticamente) |
| `run_pipeline.py` | Orquestrador — roda todos os notebooks de uma vez |
| `requirements.txt` | Dependências do projeto |

## Como rodar

Requer Python 3.11 ou superior (o projeto foi desenvolvido com Python 3.14).

### 1. Instale as dependências

```
pip install -r requirements.txt
```

### 2. Execute o pipeline

**Opção A — Orquestrador (recomendado):** roda todos os notebooks automaticamente, em ordem, com controle de erros e log de execução:

```
python run_pipeline.py
```

**Opção B — Manual:** abra os notebooks da pasta `notebooks/` e rode, em ordem, do 01 ao 07 (use *Kernel → Restart & Run All* em cada um).

### 3. Rode os testes

```
python -m pytest
```

Os notebooks 06 e 07 podem ser rodados várias vezes com o mesmo resultado. A única coluna que muda a cada execução é `data_geracao`, da tabela `metadados`.

---

## Orquestrador (`run_pipeline.py`)

O orquestrador executa os notebooks em sequência, exibe progresso em tempo real, registra um log completo em `logs/` e para imediatamente se qualquer etapa falhar — evitando que dados inconsistentes se propaguem para as camadas seguintes.

### Comandos disponíveis

| Comando | O que faz |
|---|---|
| `python run_pipeline.py` | Roda as etapas 1 a 7 |
| `python run_pipeline.py --full` | Inclui a etapa 8 (publicação no Google Planilhas) |
| `python run_pipeline.py --from 5` | Começa a partir do notebook 05 |
| `python run_pipeline.py --only 7` | Roda somente o notebook 07 |
| `python run_pipeline.py --timeout 300` | Define timeout de 5 minutos por notebook |

> A etapa 08 é opcional (`--full`) pois requer o arquivo `google_service_account.json` e o arquivo `planilha_id.txt` com o ID da planilha no Google.

### Exemplo de saída

```
═══════════════════════════════════════════════════════════════════
  PIPELINE ENGENHARIA DE DADOS — INICIANDO
  14/07/2025 10:32:01  |  7 etapa(s) agendada(s)
  Log completo: logs/pipeline_20250714_103201.log
═══════════════════════════════════════════════════════════════════

  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0%  Etapa 1/7
  Notebook : 01_tratamento_clientes.ipynb
  Descrição: Tratamento de Clientes
  ───────────────────────────────────────────────────────────────
  ✅ CONCLUÍDO em 4.3s

═══════════════════════════════════════════════════════════════════
  RESUMO DA EXECUÇÃO
═══════════════════════════════════════════════════════════════════
  Tempo total   : 1m 42s
  Executadas    : 7      ✅ Sucesso: 7      ❌ Falhas: 0
  ───────────────────────────────────────────────────────────────
  ✅ [OK    ] [   4.3s]  01_tratamento_clientes.ipynb
  ✅ [OK    ] [   6.1s]  02_tratamento_assinaturas.ipynb
  ✅ [OK    ] [   5.8s]  03_tratamento_interacoes.ipynb
  ✅ [OK    ] [   4.2s]  04_tratamento_pagamento.ipynb
  ✅ [OK    ] [   3.9s]  05_tratamento_planos.ipynb
  ✅ [OK    ] [  12.4s]  06_validacao_integridade.ipynb
  ✅ [OK    ] [  65.3s]  07_camada_gold.ipynb
═══════════════════════════════════════════════════════════════════
  🎉 Pipeline concluído com sucesso!
═══════════════════════════════════════════════════════════════════
```

---

## Notebooks

| Notebook | O que faz | Saída |
|---|---|---|
| 01 | Trata a tabela de clientes | `data/Staging/dim_clientes.csv` |
| 02 | Trata a tabela de assinaturas | `data/Staging/dim_assinatura.csv` |
| 03 | Trata a tabela de interações | `data/Staging/dim_interacoes.csv` |
| 04 | Trata a tabela de pagamentos | `data/Staging/fato_pagamentos.csv` |
| 05 | Trata a tabela de planos | `data/Staging/dim_planos.csv` |
| 06 | Valida a integridade entre as tabelas e trata órfãos | `data/Silver/` |
| 07 | Constrói e confere as 7 tabelas da camada Gold | `data/Gold/` |
| 08 | Publica as tabelas Gold no Google Planilhas | — |

### O que cada notebook de tratamento (01 a 05) faz

Todos os notebooks de tratamento seguem o mesmo padrão:

1. Lê os dados brutos da camada Bronze.
2. Remove duplicatas e valida a chave primária.
3. Trata tipos, nulos e valores inválidos.
4. Padroniza textos (strip, capitalização, dicionário de correção).
5. Converte e confere colunas de data com as funções de `src/datas.py`.
6. Gera um relatório de qualidade (`APROVADO` / `REPROVADO` por verificação).
7. Só grava o arquivo em Staging se todas as verificações passarem.

---

## Módulo `src/`

### `src/datas.py`

Funções utilitárias para conversão e validação de datas em séries Pandas.

| Função | O que faz |
|---|---|
| `converter_data(col)` | Converte strings para `datetime`. Aceita os formatos `AAAA-MM-DD` e `DD/MM/AAAA`. Valores inválidos viram `NaT`. |
| `conferir_data(convertida, original)` | Verifica se a conversão preservou o dia e o mês corretos e se nenhum valor válido virou `NaT`. Retorna `True` ou `False`. |

---

## Testes

Os testes ficam em `tests/test_datas.py` e cobrem as funções de `src/datas.py`.

| Teste | O que verifica |
|---|---|
| `test_iso_nao_troca_dia_e_mes` | Formato ISO (`AAAA-MM-DD`) não inverte dia e mês |
| `test_formato_brasileiro` | Formato brasileiro (`DD/MM/AAAA`) é reconhecido corretamente |
| `test_texto_invalido_vira_vazio` | String inválida se transforma em `NaT`, não em erro |
| `test_conferir_data_aprova_conversao_certa` | Conversão mista ISO + BR é aprovada |
| `test_conferir_data_reprova_o_bug_antigo` | Detecta o bug de inversão de dia/mês do `format="mixed"` |

Para rodar:

```
python -m pytest
```

---

## Dashboard

O dashboard lê as 7 tabelas da camada Gold diretamente do Google Planilhas e as exibe em um painel interativo.

| Arquivo | O que faz |
|---|---|
| `dashboard/Index.html` | Frontend: exibe KPIs, gráficos e tabelas. Usa Chart.js e suporta tema claro e escuro. |
| `dashboard/Code.js` | Backend (Google Apps Script): lê as abas da planilha e entrega os dados ao frontend via `getDashboardData()`. |

Para publicar o dashboard, implante o `Code.js` como um Web App no Google Apps Script e sirva o `Index.html` pela função `doGet()`.

Link do dashboard: https://script.google.com/macros/s/AKfycbxf2zWomtpNk06CUIvBKAqu8hwN_J4WMFDSQ4r5a1xjLRMz7ThVTK6zXv0o1osAm7Cj/exec

---

## Camada Gold

Os arquivos são gravados com separador `;`, decimal `,` e codificação UTF-8 com BOM. Percentuais são frações (`0,2427` = 24,27%) e datas são texto no formato `AAAA-MM-DD`.

Os nomes das tabelas e das colunas são o contrato com o dashboard: não devem ser renomeados sem atualizar o `Code.js` e o `Index.html`.

| Tabela | Uma linha = | Colunas |
|---|---|---|
| `receita_mensal` | 1 mês | `mes`, `qtd_pagamentos`, `receita_paga`, `receita_paga_original`, `ticket_medio`, `mes_incompleto` |
| `pagamentos_status_mensal` | 1 mês e 1 status | `mes`, `status_pagamento`, `qtd_pagamentos`, `valor_total`, `pct_do_mes`, `mes_incompleto` |
| `assinaturas_mensal` | 1 mês | `mes`, `novas_assinaturas`, `cancelamentos`, `assinaturas_ativas_fim_mes`, `taxa_cancelamento`, `mes_incompleto` |
| `assinaturas_por_plano` | 1 plano | `id_plano`, `nome_plano`, `categoria`, `valor_mensal`, `qtd_assinaturas`, `canceladas`, `agendadas`, `ativas`, `pct_cancelamento`, `receita_paga` |
| `interacoes_por_tipo` | 1 tipo | `tipo`, `qtd_interacoes`, `pct_do_total` |
| `metadados` | 1 linha | `mes_inicial`, `mes_final`, `data_referencia`, `mes_incompleto`, `ultimo_mes_novas_assinaturas`, `data_geracao` |
| `kpis_resumo` | 1 linha | `receita_total`, `ticket_medio`, `assinaturas_ativas`, `cancelamentos_agendados`, `pct_cancelamento`, `assinaturas_canceladas`, `assinaturas_total`, `pct_pagamentos_pagos`, `qtd_pagamentos_pagos`, `qtd_pagamentos_total`, `total_interacoes` |

> A Gold só é gravada depois que todas as conferências passam. Se qualquer uma falhar, nenhum arquivo é alterado.

### Regras de negócio da Gold

- **Receita:** somente pagamentos com status `Pago`, usando o `valor` tratado. O `valor_original` fica ao lado para comparação.
- **Cancelamentos:** só contam quando a data já chegou (até a data de referência). Data futura é cancelamento agendado, e a assinatura continua ativa.
- **Cliente de um pagamento:** sempre pela assinatura (pagamento → assinatura → cliente). O `id_cliente` direto do pagamento não é usado.
- **Data de referência:** a última data de pagamento nos dados (06/09/2026), e não a data do computador. Assim, rodar de novo gera o mesmo resultado.
- **Último mês:** incompleto, sinalizado pela coluna `mes_incompleto`.
- **Novas assinaturas:** os meses depois do último início de assinatura (abril de 2026) ficam vazios (`NaN`), e não zerados.
- **Plano "Não identificado":** aparece como uma linha própria em `assinaturas_por_plano`, sem ser escondido.
- **Ordem das linhas:** em `assinaturas_por_plano` a ordem das linhas não é garantida.

---

## Limitações conhecidas

- Os dados são fictícios.
- O cliente de um pagamento quase nunca é o dono da assinatura (14.976 de 14.984 pagamentos).
- IDs que não existem na tabela de origem viram `-1`. As colunas `*_original` guardam o ID de origem:
  - 339 assinaturas (11%) apontam para o plano `99`, que não existe.
  - 1 assinatura, 14 pagamentos e 5 interações apontam para o cliente `9999`.
  - 2 pagamentos apontam para a assinatura `77777`.
- Pagamentos com valor negativo viram positivos (30 casos, 20 deles com status `Pago`). A coluna `valor_original` guarda o valor de origem. Na receita paga, o efeito é de R$ 4.348,60.
- 139 cancelamentos têm data futura. Na Silver ficam com o status `Cancelado`, e na Gold são tratados como agendados.
- O plano "Plus" e o "Não identificado" estão sem valor mensal.
- Os pagamentos vão de 01/01/2024 a 06/09/2026, e as novas assinaturas, de janeiro de 2024 a abril de 2026.

---

## Próximos passos

- [ ] Criar `src/validacao.py` com as funções de quality gate reutilizáveis (hoje repetidas nos notebooks 01 a 05).
- [ ] Criar `src/config.py` centralizando todos os caminhos de pastas.
- [ ] Adicionar `pyproject.toml` para instalar o pacote com `pip install -e .` e eliminar os `sys.path.append()` dos notebooks.
- [ ] Ampliar os testes para cobrir as funções de tratamento dos notebooks (além de `datas.py`).
- [ ] Adicionar type hints e docstrings completas nas funções de `src/`.
- [ ] Substituir os `print()` por `logging` estruturado em `src/`.
- [ ] Criar um limite de órfãos e uma pasta de quarentena no notebook 06.
- [ ] Adicionar Ruff para lint automático do código Python.
