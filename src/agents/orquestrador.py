import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Annotated, TypedDict
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('orquestrador')

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from tools.database_tool import DatabaseTool
from tools.metrics_tool import MetricsTool
from tools.charts_tool import ChartsTool
from tools.news_tool import NewsTool
from tools.report_tool import ReportTool

class EstadoAgente(TypedDict):
    """Estado do agente durante a execução."""
    messages: Annotated[list, add_messages]
    metricas: Dict[str, Any]
    noticias: List[Dict]
    graficos: Dict[str, str]
    relatorio_gerado: bool
    audit_log: List[Dict]


def fn_calcular_metricas_srag() -> str:

    try:
        metrics = MetricsTool()
        resultado = metrics.gerar_resumo_metricas()
        logging.getLogger('orquestrador').info("Métricas calculadas com sucesso")
        return resultado
    except Exception as e:
        logging.getLogger('orquestrador').error(f"Erro ao calcular métricas: {e}")
        return f"Erro ao calcular métricas: {str(e)}"


def fn_gerar_graficos_srag() -> str:

    try:
        charts = ChartsTool()
        graficos = charts.gerar_todos_graficos()
        resultado = "Gráficos gerados:\n"
        for nome, caminho in graficos.items():
            resultado += f"- {nome}: {caminho}\n"
        logging.getLogger('orquestrador').info("Gráficos gerados com sucesso")
        return resultado
    except Exception as e:
        logging.getLogger('orquestrador').error(f"Erro ao gerar gráficos: {e}")
        return f"Erro ao gerar gráficos: {str(e)}"


def fn_buscar_noticias_srag() -> str:

    try:
        news = NewsTool()
        resultado = news.obter_resumo_noticias(max_noticias=3)
        logging.getLogger('orquestrador').info("Notícias buscadas com sucesso")
        return resultado
    except Exception as e:
        logging.getLogger('orquestrador').error(f"Erro ao buscar notícias: {e}")
        return "Não foi possível buscar notícias no momento."


def fn_consultar_estatisticas_banco() -> str:

    try:
        db = DatabaseTool()
        stats = db.obter_estatisticas_gerais()
        resultado = "Estatísticas do Banco de Dados:\n"
        for key, value in stats.items():
            resultado += f"- {key}: {value}\n"
        logging.getLogger('orquestrador').info("Estatísticas consultadas com sucesso")
        return resultado
    except Exception as e:
        logging.getLogger('orquestrador').error(f"Erro ao consultar estatísticas: {e}")
        return f"Erro ao consultar estatísticas: {str(e)}"


def fn_gerar_relatorio_pdf(analise: str = "") -> str:

    try:
        report = ReportTool()
        caminho = report.gerar_relatorio(analise_llm=analise if analise else None)
        logging.getLogger('orquestrador').info(f"Relatório PDF gerado: {caminho}")
        return f"Relatório PDF gerado com sucesso em: {caminho}"
    except Exception as e:
        logging.getLogger('orquestrador').error(f"Erro ao gerar relatório PDF: {e}")
        return f"Erro ao gerar relatório PDF: {str(e)}"


calcular_metricas_srag = StructuredTool.from_function(
    func=fn_calcular_metricas_srag,
    name="calcular_metricas_srag",
    description="Calcula todas as métricas de SRAG: taxa de aumento de casos, taxa de mortalidade, taxa de ocupação de UTI e taxa de vacinação. Use esta ferramenta para obter as métricas atualizadas do banco de dados."
)

gerar_graficos_srag = StructuredTool.from_function(
    func=fn_gerar_graficos_srag,
    name="gerar_graficos_srag",
    description="Gera os gráficos de casos de SRAG: gráfico diário (30 dias) e gráfico mensal (12 meses). Use esta ferramenta para criar visualizações dos dados."
)

buscar_noticias_srag = StructuredTool.from_function(
    func=fn_buscar_noticias_srag,
    name="buscar_noticias_srag",
    description="Busca notícias recentes sobre SRAG (Síndrome Respiratória Aguda Grave). Use esta ferramenta para obter contexto atual sobre a situação epidemiológica."
)

consultar_estatisticas_banco = StructuredTool.from_function(
    func=fn_consultar_estatisticas_banco,
    name="consultar_estatisticas_banco",
    description="Consulta estatísticas gerais do banco de dados de SRAG. Use para obter informações sobre o total de registros e período dos dados."
)

gerar_relatorio_pdf = StructuredTool.from_function(
    func=fn_gerar_relatorio_pdf,
    name="gerar_relatorio_pdf",
    description="Gera PDF do relatório. Parâmetro opcional 'analise': texto curto com análise das notícias (máx 3 frases)."
)

TOOLS = [
    calcular_metricas_srag,
    gerar_graficos_srag,
    buscar_noticias_srag,
    consultar_estatisticas_banco,
    gerar_relatorio_pdf
]

class AgenteOrquestrador:

    def __init__(self, modelo: str = "llama-3.1-8b-instant"):

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY não encontrada. "
                "Configure no arquivo .env ou variável de ambiente."
            )

        self.llm = ChatGroq(
            api_key=api_key,
            model_name=modelo,
            temperature=0.1,
            max_tokens=4096
        )

        self.llm_com_tools = self.llm.bind_tools(TOOLS)
        self.grafo = self._criar_grafo()
        self.log_auditoria = []

        logger.info(f"AgenteOrquestrador inicializado com modelo: {modelo}")

    def _registrar_auditoria(self, acao: str, detalhes: Dict[str, Any]):

        registro = {
            'timestamp': datetime.now().isoformat(),
            'acao': acao,
            'detalhes': detalhes
        }
        self.log_auditoria.append(registro)
        logger.info(f"AUDITORIA: {registro}")

    def _criar_grafo(self) -> StateGraph:

        workflow = StateGraph(EstadoAgente)
        workflow.add_node("agente", self._no_agente)
        workflow.add_node("tools", ToolNode(TOOLS))
        workflow.set_entry_point("agente")
        workflow.add_conditional_edges(
            "agente",
            self._deve_continuar,
            {
                "continuar": "tools",
                "fim": END
            }
        )
        workflow.add_edge("tools", "agente")

        return workflow.compile()

    def _no_agente(self, state: EstadoAgente) -> Dict:

        messages = state["messages"]
        response = self.llm_com_tools.invoke(messages)

        self._registrar_auditoria("resposta_agente", {
            "tipo": "tool_call" if response.tool_calls else "resposta_final",
            "conteudo": str(response.content)[:200]
        })

        return {"messages": [response]}

    def _deve_continuar(self, state: EstadoAgente) -> str:

        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continuar"

        return "fim"

    def executar(self, tarefa: str) -> Dict[str, Any]:

        logger.info(f"Iniciando execução da tarefa: {tarefa[:100]}...")

        self._registrar_auditoria("inicio_execucao", {"tarefa": tarefa})

        system_prompt = """Você é um agente que gera relatórios de SRAG.

            REGRAS:
            - Execute cada ferramenta APENAS UMA VEZ
            - Após chamar gerar_relatorio_pdf, PARE imediatamente
            - NÃO repita chamadas de ferramentas
            - Seja conciso nas respostas"""


        estado_inicial = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=tarefa)
            ],
            "metricas": {},
            "noticias": [],
            "graficos": {},
            "relatorio_gerado": False,
            "audit_log": []
        }

        try:
            resultado = self.grafo.invoke(
                estado_inicial,
                {"recursion_limit": 15}  # Limitar iterações
            )

            self._registrar_auditoria("fim_execucao", {"status": "sucesso"})

            resposta_final = resultado["messages"][-1].content

            return {
                "sucesso": True,
                "resposta": resposta_final,
                "log_auditoria": self.log_auditoria
            }

        except Exception as e:
            self._registrar_auditoria("erro_execucao", {"erro": str(e)})
            logger.error(f"Erro na execução: {e}")

            return {
                "sucesso": False,
                "erro": str(e),
                "log_auditoria": self.log_auditoria
            }

    def gerar_relatorio_completo(self) -> Dict[str, Any]:

        tarefa = """
        Execute na ordem:
        1. consultar_estatisticas_banco
        2. calcular_metricas_srag  
        3. gerar_graficos_srag
        4. buscar_noticias_srag
        5. gerar_relatorio_pdf com analise="[escreva 2-3 frases resumindo as notícias e a tendência]"
        
        PARE após gerar_relatorio_pdf.
        """

        return self.executar(tarefa)


def criar_agente(modelo: str = "llama-3.1-8b-instant") -> AgenteOrquestrador:

    return AgenteOrquestrador(modelo)

