# SRAG Health Report

Sistema baseado em **Agentes de IA** para geração automatizada de relatórios sobre **Síndrome Respiratória Aguda Grave (SRAG)** no Brasil.

## Sobre o Projeto

Este projeto foi desenvolvido como uma Prova de Conceito (PoC) para a **Indicium HealthCare Inc.**, com o objetivo de criar uma solução que auxilie profissionais da área da saúde a ter um entendimento em tempo real sobre a severidade e o avanço de surtos de doenças respiratórias.

O sistema utiliza um **agente orquestrador** que coordena múltiplas ferramentas para:
- Consultar dados de SRAG do DATASUS
- Calcular métricas epidemiológicas
- Gerar visualizações gráficas
- Buscar notícias em tempo real
- Produzir relatórios profissionais em PDF

## Métricas Calculadas

O sistema calcula **4 métricas principais**:

| Métrica | Descrição | Fórmula |
|---------|-----------|---------|
| **Taxa de Aumento de Casos** | Variação percentual entre períodos | `((atual - anterior) / anterior) × 100` |
| **Taxa de Mortalidade** | Percentual de óbitos sobre total de casos | `(óbitos / total_casos) × 100` |
| **Taxa de Ocupação de UTI** | Percentual de internados que foram para UTI | `(internações_UTI / total_internações) × 100` |
| **Taxa de Vacinação** | Percentual de vacinados entre os casos | `(vacinados / total_com_info) × 100` |

## Gráficos Gerados

- **Casos Diários**: Gráfico de barras com os últimos 30 dias + média móvel de 7 dias
- **Casos Mensais**: Gráfico de barras com os últimos 12 meses + linha de média

## 🛠Tecnologias Utilizadas

- **Python 3.x**
- **LangChain + LangGraph** - Framework de agentes
- **Groq** - LLM (llama-3.3-70b-versatile)
- **SQLite** - Banco de dados
- **Matplotlib** - Visualizações
- **ReportLab** - Geração de PDF
- **DuckDuckGo Search** - Busca de notícias
- **Pandas** - Manipulação de dados

## Estrutura do Projeto

```
srag-health-report/
├── src/
│   ├── main.py                 # Ponto de entrada do sistema
│   ├── agents/
│   │   ├── __init__.py
│   │   └── orquestrador.py     # Agente principal
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── database_tool.py    # Consultas ao banco
│   │   ├── metrics_tool.py     # Cálculo de métricas
│   │   ├── charts_tool.py      # Geração de gráficos
│   │   ├── news_tool.py        # Busca de notícias
│   │   └── report_tool.py      # Geração de PDF
│   └── data/
│       └── preprocessing.py    # Processamento dos dados
├── data/
│   ├── raw/                    # Dados brutos (CSV do DATASUS)
│   └── processed/              # Banco SQLite processado
├── docs/
│   └── arquitetura.pdf         # Diagrama de arquitetura
├── reports/                    # Relatórios gerados
│   └── charts/                 # Gráficos gerados
├── notebooks/                  # Análises exploratórias
├── .env                        # Variáveis de ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/srag-health-report.git
cd srag-health-report
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GROQ_API_KEY=sua_chave_groq_aqui
```

Para obter a chave da API Groq (gratuita):
1. Acesse [console.groq.com](https://console.groq.com)
2. Crie uma conta
3. Gere uma API key

### 5. Baixe e processe os dados

#### 5.1 Baixe os dados do DATASUS

1. Acesse: [opendatasus.saude.gov.br/dataset/srag-2021-a-2024](https://opendatasus.saude.gov.br/dataset/srag-2021-a-2024)
2. Baixe o arquivo CSV mais recente (ex: SRAG 2025)
3. Coloque o arquivo em `data/raw/`

#### 5.2 Processe os dados

```bash
python src/data/preprocessing.py data/raw/NOME_DO_ARQUIVO.csv
```

Isso criará o banco SQLite em `data/processed/srag.db`.

## 💻 Como Usar

### Modo Relatório (Padrão)

Gera um relatório completo em PDF:

```bash
python src/main.py --modo relatorio
```

O relatório será salvo em `reports/relatorio_srag_YYYYMMDD_HHMMSS.pdf`.

### Modo Interativo

Permite fazer perguntas ao agente:

```bash
python src/main.py --modo interativo
```

Exemplo de perguntas:
- "Qual a taxa de mortalidade atual?"
- "Quantos casos temos no banco de dados?"
- "Gere os gráficos de casos"

### Modo Verificação

Verifica se o sistema está configurado corretamente:

```bash
python src/main.py --modo verificar
```

## Exemplo de Uso

```bash
# 1. Verificar configuração
python src/main.py --modo verificar

# 2. Gerar relatório completo
python src/main.py --modo relatorio

# Saída esperada:
# ✅ Agente inicializado!
# 📊 Gerando relatório completo...
# ✅ Relatório gerado com sucesso!
# 📄 Arquivo: reports/relatorio_srag_20240203_143022.pdf
```

## Relatório Gerado

O relatório PDF inclui:

1. **Resumo Executivo** - Visão geral dos dados
2. **Métricas Principais** - Tabela com as 4 métricas e análises
3. **Análise Gráfica** - Gráficos de casos diários e mensais
4. **Conclusões e Recomendações** - Análise automática baseada nos dados

## Segurança

O sistema implementa as seguintes proteções:

- **Validação de Queries SQL**: Apenas comandos SELECT são permitidos
- **Proteção contra SQL Injection**: Palavras-chave perigosas são bloqueadas
- **Auditoria**: Todas as ações do agente são registradas em log
- **Tratamento de Dados Sensíveis**: Dados pessoais são removidos no pré-processamento

## Fonte dos Dados

Os dados utilizados são provenientes do **SIVEP-Gripe (Sistema de Informação de Vigilância Epidemiológica da Gripe)**, disponibilizados pelo **DATASUS/Ministério da Saúde**.

- **URL**: [opendatasus.saude.gov.br](https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026)
- **Atualização**: Semanal
- **Cobertura**: Todo o território nacional

**Observação**: Este sistema é uma PoC e não deve ser utilizado como única fonte para tomada de decisões clínicas ou de saúde pública.
