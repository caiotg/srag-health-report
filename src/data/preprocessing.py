import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import logging
import warnings

from polars.polars import first

warnings.simplefilter('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


COLUNAS_SELECIONADAS = [
    'DT_NOTIFIC',      # Data de notificação
    'SEM_NOT',         # Semana epidemiológica da notificação
    'DT_SIN_PRI',      # Data dos primeiros sintomas
    'SG_UF_NOT',       # UF de notificação
    'ID_MUNICIP',      # Município (código)
    'CS_SEXO',         # Sexo (M/F/I)
    'DT_NASC',         # Data de nascimento
    'NU_IDADE_N',      # Idade
    'TP_IDADE',        # Tipo idade (1-dia, 2-mês, 3-ano)
    'CS_GESTANT',      # Gestante
    'CS_RACA',         # Raça/Cor (1-Branca 2-Preta, 3-Amarela, 4-Parda, 5-Indígena, 9-Ignorado)
    'CS_ESCOL_N',      # Escolaridade (0-Sem escolaridade/Analfabeto, 1-Fundamental 1º ciclo (1ª a 5ª série) 2-Fundamental 2º ciclo (6ª a 9ª série), 3- Médio (1º ao 3º ano),                                   4-Superior, 5-Não se aplica, 9-Ignorado
    'NOSOCOMIAL',      # Infecção nosocomial (1-Sim, 2-Não, 9-Ignorado)
    'FEBRE',           # Sintoma: Febre (1-Sim, 2-Não, 9-Ignorado)
    'TOSSE',           # Sintoma: Tosse (1-Sim, 2-Não, 9-Ignorado)
    'GARGANTA',        # Sintoma: Dor de garganta (1-Sim, 2-Não, 9-Ignorado)
    'DISPNEIA',        # Sintoma: Dispneia (1-Sim, 2-Não, 9-Ignorado)
    'DESC_RESP',       # Sintoma: Desconforto respiratório (1-Sim, 2-Não, 9-Ignorado)
    'SATURACAO',       # Sintoma: Saturação O2 < 95% (1-Sim, 2-Não, 9-Ignorado)
    'DIARREIA',        # Sintoma: Diarreia (1-Sim, 2-Não, 9-Ignorado)
    'CARDIOPATI',      # Fator de risco: Cardiopatia (1-Sim, 2-Não, 9-Ignorado)
    'PNEUMOPATI',      # Fator de risco: Pneumopatia (1-Sim, 2-Não, 9-Ignorado)
    'RENAL',           # Fator de risco: Doença renal (1-Sim, 2-Não, 9-Ignorado)
    'OBESIDADE',       # Fator de risco: Obesidade (1-Sim, 2-Não, 9-Ignorado)
    'DIABETES',        # Fator de risco: Diabetes (1-Sim, 2-Não, 9-Ignorado)
    'UTI',             # Internação em UTI (1-Sim, 2-Não, 9-Ignorado)
    'SUPORT_VEN',      # Suporte ventilatório (1-Sim, 2-Não, 9-Ignorado)
    'VACINA_COV',      # Vacina COVID (1-Sim, 2-Não, 9-Ignorado)
    'DOSE_1_COV',      # Data 1ª dose COVID
    'DOSE_2_COV',      # Data 2ª dose COVID
    'DOSE_REF',        # Data dose reforço
    'VACINA',          # Vacina Gripe (1-Sim, 2-Não, 9-Ignorado)
    'DT_UT_DOSE',      # Data última dose
    'ANTIVIRAL',       # Uso de antiviral (1-Sim, 2-Não, 9-Ignorado)
    'HOSPITAL',        # Internação hospitalar (1-Sim, 2-Não, 9-Ignorado)
    'DT_INTERNA',      # Data de internação
    'DT_ENTUTI',       # Data entrada UTI
    'DT_SAIDUTI',      # Data saída UTI
    'DT_EVOLUCA',      # Data de evolução (desfecho)
    'EVOLUCAO',        # Evolução do caso (1-Cura, 2-Óbito, 3-Óbito outras causas, 9-Ignorado)
    'CLASSI_FIN',      # Classificação final (1-SRAG por influenza, 2-SRAG por outro vírus, 3-SRAG por outro agente, 4-SRAG não especificado, 5-SRAG por COVID-19)
    'DT_ENCERRA',      # Data de encerramento
]

def carregar_dados_brutos(caminho_csv: str, nrows: int = None) -> pd.DataFrame:

    logger.info(f"Carregando dados de: {caminho_csv}")

    try:
        df = pd.read_csv(
            caminho_csv,
            sep=';',
            nrows=nrows,
            low_memory=False
        )
        return df
    except Exception as e:
        print(f'Ocorreu um Erro: {e}')


def selecionar_colunas(df: pd.DataFrame) -> pd.DataFrame:

    colunas_disponiveis = [col for col in COLUNAS_SELECIONADAS if col in df.columns]
    colunas_faltantes = [col for col in COLUNAS_SELECIONADAS if col not in df.columns]
    
    if colunas_faltantes:
        logger.warning(f"Colunas não encontradas: {colunas_faltantes}")

    return df[colunas_disponiveis].copy()


# Avaliar se vale a pena
def remover_dados_sensiveis(df: pd.DataFrame) -> pd.DataFrame:

    colunas_sensiveis = [
        'NM_PACIENT',  # Nome do paciente
        'NM_MAE_PAC',  # Nome da mãe
        'NM_LOGRADO',  # Logradouro
        'NM_BAIRRO',   # Bairro (específico)
        'NU_CPF',      # CPF
        'NU_CNS',      # Cartão SUS
        'NU_CEP',      # CEP
        'NU_NUMERO',   # Numero Logradouro
        'NU_TELEFON',  # Telefone
        'NU_DDD_TEL',  # Telefone
    ]
    
    colunas_para_remover = [col for col in colunas_sensiveis if col in df.columns]
    
    if colunas_para_remover:
        df = df.drop(columns=colunas_para_remover)
        logger.info(f"Colunas sensíveis removidas: {colunas_para_remover}")

    if 'NU_IDADE_N' in df.columns:
        df['FAIXA_ETARIA'] = pd.cut(
            df['NU_IDADE_N'],
            bins=[0, 4, 11, 17, 29, 44, 59, 74, 200],
            labels=['0-4', '5-11', '12-17', '18-29', '30-44', '45-59', '60-74', '75+']
        )
    
    return df

def converter_datas(df: pd.DataFrame) -> pd.DataFrame:

    colunas_data = [
        'DT_NOTIFIC', 'DT_SIN_PRI', 'DT_NASC', 'DT_INTERNA',
        'DT_ENTUTI', 'DT_SAIDUTI', 'DT_EVOLUCA', 'DT_ENCERRA',
        'DOSE_1_COV', 'DOSE_2_COV', 'DOSE_REF', 'DT_UT_DOSE'
    ]
    
    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    
    return df

def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:

    if 'CS_SEXO' in df.columns:
        df['CS_SEXO'] = df['CS_SEXO'].str.upper().replace({
            'M': 'M', 'F': 'F', 'I': 'I'
        })

    colunas_booleanas = [
        'FEBRE', 'TOSSE', 'GARGANTA', 'DISPNEIA', 'DESC_RESP',
        'SATURACAO', 'DIARREIA', 'UTI', 'HOSPITAL', 'VACINA_COV', 'VACINA',
        'CARDIOPATI', 'PNEUMOPATI', 'RENAL', 'OBESIDADE', 'DIABETES'
    ]
    
    for col in colunas_booleanas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'EVOLUCAO' in df.columns:
        df['EVOLUCAO'] = pd.to_numeric(df['EVOLUCAO'], errors='coerce')
    
    return df

def adicionar_colunas_auxiliares(df: pd.DataFrame) -> pd.DataFrame:

    if 'EVOLUCAO' in df.columns:
        df['FLAG_OBITO'] = df['EVOLUCAO'].isin([2, 3]).astype(int)

    if 'UTI' in df.columns:
        df['FLAG_UTI'] = (df['UTI'] == 1).astype(int)

    if 'VACINA_COV' in df.columns:
        df['FLAG_VACINADO_COVID'] = (df['VACINA_COV'] == 1).astype(int)

    if 'VACINA' in df.columns:
        df['FLAG_VACINADO_GRIPE'] = (df['VACINA'] == 1).astype(int)

    if 'DT_NOTIFIC' in df.columns:
        df['ANO_NOTIFIC'] = df['DT_NOTIFIC'].dt.year
        df['MES_NOTIFIC'] = df['DT_NOTIFIC'].dt.month
        df['DIA_NOTIFIC'] = df['DT_NOTIFIC'].dt.day
        df['DATA_NOTIFIC_STR'] = df['DT_NOTIFIC'].dt.strftime('%Y-%m-%d')
    
    return df

def processar_dados_completo(caminho_csv: str, nrows: int = None) -> pd.DataFrame:

    logger.info("=" * 50)
    logger.info("Iniciando processamento de dados")
    logger.info("=" * 50)
    

    df = carregar_dados_brutos(caminho_csv, nrows)
    df = selecionar_colunas(df)
    df = remover_dados_sensiveis(df)
    df = converter_datas(df)
    df = limpar_dados(df)
    df = adicionar_colunas_auxiliares(df)
    
    logger.info(f"Processamento concluído: {len(df)} registros")
    logger.info(f"Colunas finais: {list(df.columns)}")
    
    return df


def salvar_sqlite(df: pd.DataFrame, caminho_db: str, tabela: str = 'srag'):

    os.makedirs(os.path.dirname(caminho_db), exist_ok=True)

    conn = sqlite3.connect(caminho_db)
    df_sqlite = df.copy()
    for col in df_sqlite.select_dtypes(include=['datetime64']).columns:
        df_sqlite[col] = df_sqlite[col].astype(str).replace('NaT', None)
    
    df_sqlite.to_sql(tabela, conn, if_exists='replace', index=False)

    cursor = conn.cursor()
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_dt_notific ON {tabela}(DT_NOTIFIC)')
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_evolucao ON {tabela}(EVOLUCAO)')
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_uf ON {tabela}(SG_UF_NOT)')
    conn.commit()
    
    logger.info(f"Dados salvos com sucesso! Tabela: {tabela}")
    conn.close()


def gerar_estatisticas(df: pd.DataFrame) -> dict:

    stats = {
        'total_registros': len(df),
        'periodo_inicio': df['DT_NOTIFIC'].min() if 'DT_NOTIFIC' in df.columns else None,
        'periodo_fim': df['DT_NOTIFIC'].max() if 'DT_NOTIFIC' in df.columns else None,
        'total_obitos': df['FLAG_OBITO'].sum() if 'FLAG_OBITO' in df.columns else None,
        'total_uti': df['FLAG_UTI'].sum() if 'FLAG_UTI' in df.columns else None,
        'taxa_mortalidade': (df['FLAG_OBITO'].sum() / len(df) * 100) if 'FLAG_OBITO' in df.columns else None,
        'estados_unicos': df['SG_UF_NOT'].nunique() if 'SG_UF_NOT' in df.columns else None,
    }
    
    return stats


if __name__ == "__main__":
    import sys
    CAMINHO_CSV = r"data\raw\INFLUD25-22-12-2025.csv"
    CAMINHO_DB = r"data\processed\srag.db"

    if len(sys.argv) > 1:
        CAMINHO_CSV = sys.argv[1]

    if not os.path.exists(CAMINHO_CSV):
        logger.error(f"Arquivo não encontrado: {CAMINHO_CSV}")
        sys.exit(1)

    df = processar_dados_completo(CAMINHO_CSV, nrows=None)

    stats = gerar_estatisticas(df)

    for key, value in stats.items():
        print(f"{key}: {value}")

    salvar_sqlite(df, CAMINHO_DB)

    print(f"Banco de dados salvo em: {CAMINHO_DB}")
