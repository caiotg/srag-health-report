import sqlite3
import pandas as pd
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_tool')

def get_project_root():

    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):  # Máximo 5 níveis
        data_path = os.path.join(current, 'data', 'processed')
        if os.path.exists(data_path):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # Chegou na raiz do sistema
            break
        current = parent

    return os.getcwd()


def get_default_db_path():

    root = get_project_root()
    return os.path.join(root, 'data', 'processed', 'srag.db')


class DatabaseTool:

    TABELAS_PERMITIDAS = ['srag']
    KEYWORDS_BLOQUEADAS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
        'TRUNCATE', 'EXEC', 'EXECUTE', '--', ';--', '/*', '*/',
        'UNION SELECT', 'OR 1=1', 'OR 1 = 1'
    ]

    def __init__(self, db_path: str = None):

        self.db_path = db_path if db_path else get_default_db_path()
        self._validar_banco()
        logger.info(f"DatabaseTool inicializado com banco: {self.db_path}")

    def _validar_banco(self):

        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Banco de dados não encontrado: {self.db_path}\n"
                "Execute primeiro: python src/data/preprocessing.py"
            )

    def _validar_query(self, query: str) -> bool:

        query_upper = query.upper().strip()

        if not query_upper.startswith('SELECT'):
            logger.warning(f"Query bloqueada - não é SELECT: {query[:50]}")
            return False
        for keyword in self.KEYWORDS_BLOQUEADAS:
            if keyword.upper() in query_upper:
                logger.warning(f"Query bloqueada - keyword perigosa '{keyword}': {query[:50]}")
                return False

        return True

    def _registrar_auditoria(self, query: str, sucesso: bool, erro: str = None):

        registro = {
            'timestamp': datetime.now().isoformat(),
            'query': query[:500],  # Limitar tamanho
            'sucesso': sucesso,
            'erro': erro
        }
        logger.info(f"AUDITORIA: {registro}")

    def executar_query(self, query: str) -> pd.DataFrame:

        if not self._validar_query(query):
            self._registrar_auditoria(query, False, "Query não permitida")
            raise ValueError("Query não permitida. Apenas SELECT é aceito.")

        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()

            self._registrar_auditoria(query, True)
            logger.info(f"Query executada com sucesso. Retornou {len(df)} registros.")

            return df

        except Exception as e:
            self._registrar_auditoria(query, False, str(e))
            logger.error(f"Erro ao executar query: {e}")
            raise

    def contar_registros(self, filtro: str = None) -> int:

        query = "SELECT COUNT(*) as total FROM srag"
        if filtro:
            # Guardrail: sanitizar filtro básico
            filtro_limpo = filtro.replace(';', '').replace('--', '')
            query += f" WHERE {filtro_limpo}"

        df = self.executar_query(query)
        return int(df['total'].iloc[0])

    def obter_periodo_dados(self) -> Dict[str, str]:

        query = """
                SELECT MIN(DT_NOTIFIC) as data_inicio, \
                       MAX(DT_NOTIFIC) as data_fim
                FROM srag
                WHERE DT_NOTIFIC IS NOT NULL \
                """
        df = self.executar_query(query)

        return {
            'data_inicio': df['data_inicio'].iloc[0],
            'data_fim': df['data_fim'].iloc[0]
        }

    def casos_por_dia(self, dias: int = 30) -> pd.DataFrame:

        query = f"""
            SELECT 
                DATE(DT_NOTIFIC) as data,
                COUNT(*) as total_casos
            FROM srag
            WHERE DT_NOTIFIC IS NOT NULL
              AND DT_NOTIFIC >= DATE('now', '-{dias} days')
            GROUP BY DATE(DT_NOTIFIC)
            ORDER BY data
        """
        return self.executar_query(query)

    def casos_por_mes(self, meses: int = 12) -> pd.DataFrame:

        query = f"""
            SELECT 
                strftime('%Y-%m', DT_NOTIFIC) as ano_mes,
                COUNT(*) as total_casos
            FROM srag
            WHERE DT_NOTIFIC IS NOT NULL
              AND DT_NOTIFIC >= DATE('now', '-{meses} months')
            GROUP BY strftime('%Y-%m', DT_NOTIFIC)
            ORDER BY ano_mes
        """
        return self.executar_query(query)

    def obter_dados_obitos(self) -> pd.DataFrame:

        query = """
                SELECT COUNT(*)                                            as total_casos, \
                       SUM(CASE WHEN EVOLUCAO IN (2, 3) THEN 1 ELSE 0 END) as total_obitos, \
                       SUM(CASE WHEN EVOLUCAO = 2 THEN 1 ELSE 0 END)       as obitos_srag, \
                       SUM(CASE WHEN EVOLUCAO = 3 THEN 1 ELSE 0 END)       as obitos_outras_causas
                FROM srag
                WHERE EVOLUCAO IS NOT NULL \
                """
        return self.executar_query(query)

    def obter_dados_uti(self) -> pd.DataFrame:

        query = """
                SELECT COUNT(*)                                 as total_internacoes, \
                       SUM(CASE WHEN UTI = 1 THEN 1 ELSE 0 END) as internacoes_uti, \
                       SUM(CASE WHEN UTI = 2 THEN 1 ELSE 0 END) as nao_uti
                FROM srag
                WHERE HOSPITAL = 1 \
                """
        return self.executar_query(query)

    def obter_dados_vacinacao(self) -> pd.DataFrame:

        query = """
                SELECT COUNT(*)                                        as total_casos, \
                       SUM(CASE WHEN VACINA_COV = 1 THEN 1 ELSE 0 END) as vacinados_covid, \
                       SUM(CASE WHEN VACINA_COV = 2 THEN 1 ELSE 0 END) as nao_vacinados_covid, \
                       SUM(CASE WHEN VACINA = 1 THEN 1 ELSE 0 END)     as vacinados_gripe, \
                       SUM(CASE WHEN VACINA = 2 THEN 1 ELSE 0 END)     as nao_vacinados_gripe
                FROM srag \
                """
        return self.executar_query(query)

    def obter_aumento_casos(self, periodo_dias: int = 7) -> pd.DataFrame:

        query = f"""
            SELECT 
                SUM(CASE 
                    WHEN DATE(DT_NOTIFIC) >= DATE((SELECT MAX(DATE(DT_NOTIFIC)) FROM srag), '-{periodo_dias} days') 
                    THEN 1 ELSE 0 
                END) as casos_periodo_atual,
                SUM(CASE 
                    WHEN DATE(DT_NOTIFIC) >= DATE((SELECT MAX(DATE(DT_NOTIFIC)) FROM srag), '-{periodo_dias * 2} days')
                     AND DATE(DT_NOTIFIC) < DATE((SELECT MAX(DATE(DT_NOTIFIC)) FROM srag), '-{periodo_dias} days')
                    THEN 1 ELSE 0 
                END) as casos_periodo_anterior,
                (SELECT MAX(DATE(DT_NOTIFIC)) FROM srag) as data_referencia
            FROM srag
            WHERE DT_NOTIFIC IS NOT NULL
        """
        return self.executar_query(query)

    def obter_estatisticas_gerais(self) -> Dict[str, Any]:

        query = """
                SELECT COUNT(*)                  as total_registros, \
                       COUNT(DISTINCT SG_UF_NOT) as total_estados, \
                       MIN(DT_NOTIFIC)           as primeira_notificacao, \
                       MAX(DT_NOTIFIC)           as ultima_notificacao
                FROM srag \
                """
        df = self.executar_query(query)

        return {
            'total_registros': int(df['total_registros'].iloc[0]),
            'total_estados': int(df['total_estados'].iloc[0]),
            'primeira_notificacao': df['primeira_notificacao'].iloc[0],
            'ultima_notificacao': df['ultima_notificacao'].iloc[0]
        }


def criar_database_tool(db_path: str = "data/processed/srag.db") -> DatabaseTool:

    return DatabaseTool(db_path)

if __name__ == "__main__":

    try:
        db = DatabaseTool()

        stats = db.obter_estatisticas_gerais()
        for key, value in stats.items():
            print(f"{key}: {value}")

        periodo = db.obter_periodo_dados()
        print(f"De: {periodo['data_inicio']}")
        print(f"Até: {periodo['data_fim']}")

        obitos = db.obter_dados_obitos()
        print(obitos.to_string(index=False))

        uti = db.obter_dados_uti()
        print(uti.to_string(index=False))

        vacina = db.obter_dados_vacinacao()
        print(vacina.to_string(index=False))

        casos_dia = db.casos_por_dia(dias=7)
        print(casos_dia.to_string(index=False))

        try:
            db.executar_query("DROP TABLE srag")
        except ValueError as e:
            print(f"Bloqueado corretamente: {e}")

    except FileNotFoundError as e:
        print(f"\n Erro: {e}")
