"""
Tool de Gráficos - Geração de visualizações para o relatório SRAG
Gera os 2 gráficos exigidos:
1. Número diário de casos (últimos 30 dias de dados disponíveis)
2. Número mensal de casos (últimos 12 meses de dados disponíveis)
"""
# Configurar backend ANTES de importar pyplot
import matplotlib

matplotlib.use('Agg')  # Backend não-interativo (evita erro do Tkinter)

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import os
import logging
from typing import Optional, Tuple
from datetime import datetime

# Importar o DatabaseTool
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.database_tool import DatabaseTool, get_project_root

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charts_tool')

# Configurar estilo dos gráficos
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    try:
        plt.style.use('ggplot')
    except:
        pass  # Usar estilo padrão

plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


class ChartsTool:
    """
    Ferramenta para geração de gráficos do relatório SRAG.
    """

    def __init__(self, db_path: str = None,
                 output_dir: str = None):
        """
        Inicializa a ferramenta de gráficos.

        Args:
            db_path: Caminho para o banco de dados SQLite
            output_dir: Diretório para salvar os gráficos
        """
        self.db = DatabaseTool(db_path)

        # Definir diretório de output
        if output_dir is None:
            root = get_project_root()
            output_dir = os.path.join(root, 'reports', 'charts')

        self.output_dir = output_dir

        # Criar diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"ChartsTool inicializado. Output: {output_dir}")

    def _registrar_geracao(self, grafico: str, caminho: str):
        """Registra a geração do gráfico para auditoria."""
        registro = {
            'timestamp': datetime.now().isoformat(),
            'grafico': grafico,
            'caminho': caminho
        }
        logger.info(f"AUDITORIA GRÁFICO: {registro}")

    def _obter_ultimos_dias(self, dias: int = 30) -> pd.DataFrame:
        """
        Obtém os últimos N dias de dados DISPONÍVEIS no banco.
        Não usa DATE('now'), usa a data máxima dos dados.
        """
        query = f"""
            SELECT 
                DATE(DT_NOTIFIC) as data,
                COUNT(*) as total_casos
            FROM srag
            WHERE DT_NOTIFIC IS NOT NULL
              AND DATE(DT_NOTIFIC) >= (
                  SELECT DATE(MAX(DT_NOTIFIC), '-{dias} days') FROM srag
              )
            GROUP BY DATE(DT_NOTIFIC)
            ORDER BY data
        """
        return self.db.executar_query(query)

    def _obter_ultimos_meses(self, meses: int = 12) -> pd.DataFrame:
        """
        Obtém os últimos N meses de dados DISPONÍVEIS no banco.
        Não usa DATE('now'), usa a data máxima dos dados.
        """
        query = f"""
            SELECT 
                strftime('%Y-%m', DT_NOTIFIC) as ano_mes,
                COUNT(*) as total_casos
            FROM srag
            WHERE DT_NOTIFIC IS NOT NULL
              AND DT_NOTIFIC >= (
                  SELECT DATE(MAX(DT_NOTIFIC), '-{meses} months') FROM srag
              )
            GROUP BY strftime('%Y-%m', DT_NOTIFIC)
            ORDER BY ano_mes
        """
        return self.db.executar_query(query)

    def gerar_grafico_casos_diarios(self, dias: int = 30,
                                    salvar: bool = True) -> Tuple[plt.Figure, str]:
        """
        Gera gráfico de casos diários dos últimos N dias de dados disponíveis.

        Args:
            dias: Número de dias (padrão: 30)
            salvar: Se deve salvar o arquivo

        Returns:
            Tuple com (figura, caminho_do_arquivo)
        """
        logger.info(f"Gerando gráfico de casos diários (últimos {dias} dias de dados)")

        # Obter dados usando a data máxima disponível
        df = self._obter_ultimos_dias(dias)

        if df.empty:
            logger.warning("Sem dados para gerar gráfico de casos diários")
            return None, None

        # Converter data
        df['data'] = pd.to_datetime(df['data'])

        # Criar figura
        fig, ax = plt.subplots(figsize=(14, 6))

        # Plotar barras
        bars = ax.bar(df['data'], df['total_casos'],
                      color='#3498db', alpha=0.8, edgecolor='#2980b9')

        # Adicionar linha de tendência
        ax.plot(df['data'], df['total_casos'].rolling(window=7, min_periods=1).mean(),
                color='#e74c3c', linewidth=2, label='Média móvel (7 dias)')

        # Configurar eixos
        ax.set_xlabel('Data', fontsize=12)
        ax.set_ylabel('Número de Casos', fontsize=12)

        # Título com período real dos dados
        data_inicio = df['data'].min().strftime('%d/%m/%Y')
        data_fim = df['data'].max().strftime('%d/%m/%Y')
        ax.set_title(f'Casos Diários de SRAG\n{data_inicio} a {data_fim}',
                     fontsize=14, fontweight='bold')

        # Formatar datas no eixo X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, dias // 10)))
        plt.xticks(rotation=45, ha='right')

        # Adicionar grid
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)

        # Legenda
        ax.legend(loc='upper right')

        # Adicionar anotações
        total_periodo = df['total_casos'].sum()
        media_diaria = df['total_casos'].mean()
        ax.text(0.02, 0.98, f'Total no período: {total_periodo:,}\nMédia diária: {media_diaria:,.0f}',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        # Salvar
        caminho = None
        if salvar:
            caminho = os.path.join(self.output_dir, 'casos_diarios.png')
            fig.savefig(caminho, dpi=150, bbox_inches='tight')
            self._registrar_geracao('casos_diarios', caminho)
            logger.info(f"Gráfico salvo em: {caminho}")

        plt.close(fig)  # Fechar figura para liberar memória
        return fig, caminho

    def gerar_grafico_casos_mensais(self, meses: int = 12,
                                    salvar: bool = True) -> Tuple[plt.Figure, str]:
        """
        Gera gráfico de casos mensais dos últimos N meses de dados disponíveis.

        Args:
            meses: Número de meses (padrão: 12)
            salvar: Se deve salvar o arquivo

        Returns:
            Tuple com (figura, caminho_do_arquivo)
        """
        logger.info(f"Gerando gráfico de casos mensais (últimos {meses} meses de dados)")

        # Obter dados usando a data máxima disponível
        df = self._obter_ultimos_meses(meses)

        if df.empty:
            logger.warning("Sem dados para gerar gráfico de casos mensais")
            return None, None

        # Criar figura
        fig, ax = plt.subplots(figsize=(14, 6))

        # Cores gradientes para as barras (usando numpy ao invés de pd.np)
        cores = plt.cm.Blues(np.linspace(0.4, 0.9, len(df)))

        # Plotar barras
        bars = ax.bar(df['ano_mes'], df['total_casos'], color=cores,
                      edgecolor='#2c3e50', linewidth=1)

        # Adicionar valores nas barras
        for bar, valor in zip(bars, df['total_casos']):
            height = bar.get_height()
            ax.annotate(f'{valor:,}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, rotation=0)

        # Configurar eixos
        ax.set_xlabel('Mês/Ano', fontsize=12)
        ax.set_ylabel('Número de Casos', fontsize=12)
        ax.set_title(f'Casos Mensais de SRAG - Últimos {len(df)} Meses',
                     fontsize=14, fontweight='bold')

        plt.xticks(rotation=45, ha='right')

        # Adicionar grid
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)

        # Adicionar linha de média
        media = df['total_casos'].mean()
        ax.axhline(y=media, color='#e74c3c', linestyle='--',
                   linewidth=2, label=f'Média: {media:,.0f}')
        ax.legend(loc='upper right')

        # Adicionar anotações
        total_periodo = df['total_casos'].sum()
        ax.text(0.02, 0.98, f'Total no período: {total_periodo:,}',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        # Salvar
        caminho = None
        if salvar:
            caminho = os.path.join(self.output_dir, 'casos_mensais.png')
            fig.savefig(caminho, dpi=150, bbox_inches='tight')
            self._registrar_geracao('casos_mensais', caminho)
            logger.info(f"Gráfico salvo em: {caminho}")

        plt.close(fig)  # Fechar figura para liberar memória
        return fig, caminho

    def gerar_todos_graficos(self) -> dict:
        """
        Gera todos os gráficos necessários para o relatório.

        Returns:
            Dicionário com os caminhos dos gráficos gerados
        """
        logger.info("Gerando todos os gráficos...")

        graficos = {}

        # Gráfico 1: Casos diários
        _, caminho_diario = self.gerar_grafico_casos_diarios()
        if caminho_diario:
            graficos['casos_diarios'] = caminho_diario

        # Gráfico 2: Casos mensais
        _, caminho_mensal = self.gerar_grafico_casos_mensais()
        if caminho_mensal:
            graficos['casos_mensais'] = caminho_mensal

        logger.info(f"Gráficos gerados: {list(graficos.keys())}")
        return graficos


# =============================================================================
# Funções para uso com LangChain
# =============================================================================

def criar_charts_tool(db_path: str = None,
                      output_dir: str = None) -> ChartsTool:
    """Factory function para criar instância do ChartsTool."""
    return ChartsTool(db_path, output_dir)


def tool_gerar_grafico_diario() -> str:
    """Gera gráfico de casos diários dos últimos 30 dias de dados disponíveis."""
    charts = ChartsTool()
    _, caminho = charts.gerar_grafico_casos_diarios()
    return f"Gráfico de casos diários gerado em: {caminho}"


def tool_gerar_grafico_mensal() -> str:
    """Gera gráfico de casos mensais dos últimos 12 meses de dados disponíveis."""
    charts = ChartsTool()
    _, caminho = charts.gerar_grafico_casos_mensais()
    return f"Gráfico de casos mensais gerado em: {caminho}"


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO CHARTS TOOL")
    print("=" * 60)

    try:
        # Inicializar tool
        charts = ChartsTool()

        # Gerar todos os gráficos
        print("\nGerando gráficos...")
        graficos = charts.gerar_todos_graficos()

        print("\n✅ Gráficos gerados:")
        for nome, caminho in graficos.items():
            print(f"   {nome}: {caminho}")

        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n❌ Erro: {e}")
        print("Execute primeiro o preprocessing.py para criar o banco de dados.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback

        traceback.print_exc()