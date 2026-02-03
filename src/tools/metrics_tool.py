import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.database_tool import DatabaseTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('metrics_tool')


@dataclass
class MetricaResultado:

    nome: str
    valor: float
    unidade: str
    descricao: str
    dados_brutos: Dict[str, Any]
    data_calculo: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nome': self.nome,
            'valor': self.valor,
            'unidade': self.unidade,
            'descricao': self.descricao,
            'dados_brutos': self.dados_brutos,
            'data_calculo': self.data_calculo
        }

    def formatar(self) -> str:

        if self.unidade == '%':
            return f"{self.nome}: {self.valor:.2f}%"
        return f"{self.nome}: {self.valor:.2f} {self.unidade}"


class MetricsTool:

    def __init__(self, db_path: str = "data/processed/srag.db"):

        self.db = DatabaseTool(db_path)
        logger.info("MetricsTool inicializado")

    def _registrar_calculo(self, metrica: str, resultado: Dict[str, Any]):
        registro = {
            'timestamp': datetime.now().isoformat(),
            'metrica': metrica,
            'resultado': resultado
        }
        logger.info(f"AUDITORIA MÉTRICA: {registro}")

    def calcular_taxa_aumento_casos(self, periodo_dias: int = 7) -> MetricaResultado:

        logger.info(f"Calculando taxa de aumento de casos (período: {periodo_dias} dias)")

        df = self.db.obter_aumento_casos(periodo_dias)

        casos_atual = int(df['casos_periodo_atual'].iloc[0] or 0)
        casos_anterior = int(df['casos_periodo_anterior'].iloc[0] or 0)
        data_referencia = df['data_referencia'].iloc[0] if 'data_referencia' in df.columns else 'N/A'

        # Evitar divisão por zero
        if casos_anterior == 0:
            taxa = 0.0 if casos_atual == 0 else 100.0
        else:
            taxa = ((casos_atual - casos_anterior) / casos_anterior) * 100

        dados_brutos = {
            'casos_periodo_atual': casos_atual,
            'casos_periodo_anterior': casos_anterior,
            'periodo_dias': periodo_dias,
            'data_referencia': data_referencia
        }

        # Descrição contextualizada
        if taxa > 0:
            descricao = f"Aumento de {taxa:.1f}% nos casos em relação ao período anterior (ref: {data_referencia})"
        elif taxa < 0:
            descricao = f"Redução de {abs(taxa):.1f}% nos casos em relação ao período anterior (ref: {data_referencia})"
        else:
            descricao = f"Casos estáveis em relação ao período anterior (ref: {data_referencia})"

        resultado = MetricaResultado(
            nome="Taxa de Aumento de Casos",
            valor=round(taxa, 2),
            unidade="%",
            descricao=descricao,
            dados_brutos=dados_brutos,
            data_calculo=datetime.now().isoformat()
        )

        self._registrar_calculo("taxa_aumento_casos", resultado.to_dict())
        return resultado

    def calcular_taxa_mortalidade(self) -> MetricaResultado:

        logger.info("Calculando taxa de mortalidade")

        df = self.db.obter_dados_obitos()

        total_casos = int(df['total_casos'].iloc[0] or 0)
        total_obitos = int(df['total_obitos'].iloc[0] or 0)
        obitos_srag = int(df['obitos_srag'].iloc[0] or 0)
        obitos_outras = int(df['obitos_outras_causas'].iloc[0] or 0)

        if total_casos == 0:
            taxa = 0.0
        else:
            taxa = (total_obitos / total_casos) * 100

        dados_brutos = {
            'total_casos': total_casos,
            'total_obitos': total_obitos,
            'obitos_srag': obitos_srag,
            'obitos_outras_causas': obitos_outras
        }

        if taxa >= 10:
            severidade = "muito alta"
        elif taxa >= 5:
            severidade = "alta"
        elif taxa >= 2:
            severidade = "moderada"
        else:
            severidade = "baixa"

        descricao = f"Taxa de mortalidade {severidade}: {taxa:.2f}% dos casos evoluíram para óbito"

        resultado = MetricaResultado(
            nome="Taxa de Mortalidade",
            valor=round(taxa, 2),
            unidade="%",
            descricao=descricao,
            dados_brutos=dados_brutos,
            data_calculo=datetime.now().isoformat()
        )

        self._registrar_calculo("taxa_mortalidade", resultado.to_dict())
        return resultado

    def calcular_taxa_ocupacao_uti(self) -> MetricaResultado:

        logger.info("Calculando taxa de ocupação de UTI")

        df = self.db.obter_dados_uti()

        total_internacoes = int(df['total_internacoes'].iloc[0] or 0)
        internacoes_uti = int(df['internacoes_uti'].iloc[0] or 0)

        # Evitar divisão por zero
        if total_internacoes == 0:
            taxa = 0.0
        else:
            taxa = (internacoes_uti / total_internacoes) * 100

        dados_brutos = {
            'total_internacoes': total_internacoes,
            'internacoes_uti': internacoes_uti,
            'internacoes_nao_uti': int(df['nao_uti'].iloc[0] or 0)
        }

        if taxa >= 30:
            pressao = "crítica"
        elif taxa >= 20:
            pressao = "alta"
        elif taxa >= 10:
            pressao = "moderada"
        else:
            pressao = "baixa"

        descricao = f"Pressão {pressao} sobre UTIs: {taxa:.2f}% dos internados necessitaram de UTI"

        resultado = MetricaResultado(
            nome="Taxa de Ocupação de UTI",
            valor=round(taxa, 2),
            unidade="%",
            descricao=descricao,
            dados_brutos=dados_brutos,
            data_calculo=datetime.now().isoformat()
        )

        self._registrar_calculo("taxa_ocupacao_uti", resultado.to_dict())
        return resultado

    def calcular_taxa_vacinacao(self) -> MetricaResultado:

        logger.info("Calculando taxa de vacinação")

        df = self.db.obter_dados_vacinacao()

        total_casos = int(df['total_casos'].iloc[0] or 0)
        vacinados_covid = int(df['vacinados_covid'].iloc[0] or 0)
        nao_vacinados_covid = int(df['nao_vacinados_covid'].iloc[0] or 0)
        vacinados_gripe = int(df['vacinados_gripe'].iloc[0] or 0)

        total_com_info = vacinados_covid + nao_vacinados_covid

        if total_com_info == 0:
            taxa_covid = 0.0
        else:
            taxa_covid = (vacinados_covid / total_com_info) * 100

        dados_brutos = {
            'total_casos': total_casos,
            'vacinados_covid': vacinados_covid,
            'nao_vacinados_covid': nao_vacinados_covid,
            'vacinados_gripe': vacinados_gripe,
            'total_com_info_vacina': total_com_info
        }

        if taxa_covid >= 70:
            cobertura = "boa"
        elif taxa_covid >= 50:
            cobertura = "moderada"
        else:
            cobertura = "baixa"

        descricao = f"Cobertura vacinal {cobertura}: {taxa_covid:.2f}% dos casos com informação estavam vacinados contra COVID"

        resultado = MetricaResultado(
            nome="Taxa de Vacinação (COVID)",
            valor=round(taxa_covid, 2),
            unidade="%",
            descricao=descricao,
            dados_brutos=dados_brutos,
            data_calculo=datetime.now().isoformat()
        )

        self._registrar_calculo("taxa_vacinacao", resultado.to_dict())
        return resultado

    def calcular_todas_metricas(self) -> Dict[str, MetricaResultado]:

        logger.info("Calculando todas as métricas...")

        metricas = {
            'taxa_aumento_casos': self.calcular_taxa_aumento_casos(),
            'taxa_mortalidade': self.calcular_taxa_mortalidade(),
            'taxa_ocupacao_uti': self.calcular_taxa_ocupacao_uti(),
            'taxa_vacinacao': self.calcular_taxa_vacinacao()
        }

        logger.info("Todas as métricas calculadas com sucesso")
        return metricas

    def gerar_resumo_metricas(self) -> str:

        metricas = self.calcular_todas_metricas()

        resumo = []
        resumo.append("=" * 60)
        resumo.append("RESUMO DAS MÉTRICAS - SRAG")
        resumo.append(f"Data do cálculo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        resumo.append("=" * 60)

        for nome, metrica in metricas.items():
            resumo.append(f"\n📊 {metrica.formatar()}")
            resumo.append(f"   {metrica.descricao}")

        resumo.append("\n" + "=" * 60)

        return "\n".join(resumo)




def criar_metrics_tool(db_path: str = "data/processed/srag.db") -> MetricsTool:

    return MetricsTool(db_path)


# Funções individuais para usar como tools do LangChain
def tool_taxa_aumento_casos(periodo_dias: int = 7) -> str:

    metrics = MetricsTool()
    resultado = metrics.calcular_taxa_aumento_casos(periodo_dias)
    return f"{resultado.formatar()}\n{resultado.descricao}"


def tool_taxa_mortalidade() -> str:

    metrics = MetricsTool()
    resultado = metrics.calcular_taxa_mortalidade()
    return f"{resultado.formatar()}\n{resultado.descricao}"


def tool_taxa_ocupacao_uti() -> str:

    metrics = MetricsTool()
    resultado = metrics.calcular_taxa_ocupacao_uti()
    return f"{resultado.formatar()}\n{resultado.descricao}"


def tool_taxa_vacinacao() -> str:

    metrics = MetricsTool()
    resultado = metrics.calcular_taxa_vacinacao()
    return f"{resultado.formatar()}\n{resultado.descricao}"


if __name__ == "__main__":

    try:

        metrics = MetricsTool()
        print(metrics.gerar_resumo_metricas())

        todas = metrics.calcular_todas_metricas()
        for nome, metrica in todas.items():
            print(f"\n{nome}:")
            for key, value in metrica.dados_brutos.items():
                print(f"   {key}: {value}")

    except FileNotFoundError as e:
        print(f"\n Erro: {e}")