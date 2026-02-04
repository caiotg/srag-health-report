import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.database_tool import DatabaseTool, get_project_root
from tools.metrics_tool import MetricsTool
from tools.charts_tool import ChartsTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('report_tool')


class ReportTool:

    def __init__(self, output_dir: str = None):

        if output_dir is None:
            root = get_project_root()
            output_dir = os.path.join(root, 'reports')

        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.db = DatabaseTool()
        self.metrics = MetricsTool()
        self.charts = ChartsTool()

        self.styles = getSampleStyleSheet()
        self._configurar_estilos()

        logger.info(f"ReportTool inicializado. Output: {output_dir}")

    def _configurar_estilos(self):

        self.styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))

        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#34495e')
        ))

        self.styles.add(ParagraphStyle(
            name='Secao',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#2980b9')
        ))

        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='Destaque',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#e74c3c'),
            spaceBefore=5,
            spaceAfter=5
        ))

        self.styles.add(ParagraphStyle(
            name='Rodape',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))

    def _criar_cabecalho(self, elements: List):

        elements.append(Paragraph(
            "Relatório de Síndrome Respiratória Aguda Grave (SRAG)",
            self.styles['TituloPrincipal']
        ))

        data_atual = datetime.now().strftime('%d de %B de %Y')
        elements.append(Paragraph(
            f"Análise Epidemiológica - {data_atual}",
            self.styles['Subtitulo']
        ))

        elements.append(Spacer(1, 20))

        elements.append(Table(
            [['']],
            colWidths=[17 * cm],
            style=TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor('#3498db'))
            ])
        ))

        elements.append(Spacer(1, 20))

    def _criar_resumo_executivo(self, elements: List, metricas: Dict[str, Any], stats: Dict[str, Any]):

        elements.append(Paragraph("1. Resumo Executivo", self.styles['Secao']))

        texto_resumo = f"""
        Este relatório apresenta uma análise detalhada da situação atual da Síndrome Respiratória 
        Aguda Grave (SRAG) no Brasil, com base nos dados do Sistema de Informação de Vigilância 
        Epidemiológica da Gripe (SIVEP-Gripe) disponibilizados pelo DATASUS.
        <br/><br/>
        O banco de dados analisado contém <b>{stats.get('total_registros', 'N/A'):,}</b> registros, 
        abrangendo o período de <b>{stats.get('primeira_notificacao', 'N/A')}</b> a 
        <b>{stats.get('ultima_notificacao', 'N/A')}</b>, cobrindo <b>{stats.get('total_estados', 'N/A')}</b> 
        unidades federativas.
        """
        elements.append(Paragraph(texto_resumo, self.styles['TextoNormal']))
        elements.append(Spacer(1, 10))

    def _criar_secao_metricas(self, elements: List, metricas: Dict[str, Any]):

        elements.append(Paragraph("2. Métricas Principais", self.styles['Secao']))

        elements.append(Paragraph(
            "As métricas abaixo foram calculadas com base nos dados mais recentes disponíveis:",
            self.styles['TextoNormal']
        ))
        elements.append(Spacer(1, 10))

        dados_tabela = [
            ['Métrica', 'Valor']
        ]

        for nome, metrica in metricas.items():
            valor_formatado = f"{metrica.valor:.2f}{metrica.unidade}"
            dados_tabela.append([
                metrica.nome,
                valor_formatado
            ])

        tabela = Table(dados_tabela, colWidths=[5 * cm, 3 * cm])
        tabela.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),

            # Bordas e cores alternadas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(tabela)
        elements.append(Spacer(1, 15))

        elements.append(Paragraph("2.1 Análise das Métricas", self.styles['Subtitulo']))

        for nome, metrica in metricas.items():
            elements.append(Paragraph(
                f"<b>{metrica.nome}:</b> {metrica.descricao}",
                self.styles['TextoNormal']
            ))

    def _criar_secao_graficos(self, elements: List, graficos: Dict[str, str]):

        elements.append(PageBreak())
        elements.append(Paragraph("3. Análise Gráfica", self.styles['Secao']))

        elements.append(Paragraph(
            "Os gráficos abaixo apresentam a evolução temporal dos casos de SRAG:",
            self.styles['TextoNormal']
        ))
        elements.append(Spacer(1, 10))

        if 'casos_diarios' in graficos and os.path.exists(graficos['casos_diarios']):
            elements.append(Paragraph("3.1 Casos Diários (Últimos 30 dias)", self.styles['Subtitulo']))

            img = Image(graficos['casos_diarios'], width=16 * cm, height=8 * cm)
            elements.append(img)

            elements.append(Paragraph(
                """O gráfico acima mostra a distribuição diária de casos de SRAG no período analisado. 
                A linha vermelha representa a média móvel de 7 dias, que ajuda a identificar tendências 
                eliminando variações diárias.""",
                self.styles['TextoNormal']
            ))
            elements.append(Spacer(1, 15))

        if 'casos_mensais' in graficos and os.path.exists(graficos['casos_mensais']):
            elements.append(Paragraph("3.2 Casos Mensais (Últimos 12 meses)", self.styles['Subtitulo']))

            img = Image(graficos['casos_mensais'], width=16 * cm, height=8 * cm)
            elements.append(img)

            elements.append(Paragraph(
                """O gráfico mensal permite visualizar a sazonalidade da doença e identificar 
                períodos de maior incidência. A linha tracejada indica a média mensal do período.""",
                self.styles['TextoNormal']
            ))

    def _criar_secao_noticias(self, elements: List, noticias: List[Dict]):

        elements.append(PageBreak())
        elements.append(Paragraph("4. Notícias Recentes sobre SRAG", self.styles['Secao']))

        if not noticias:
            elements.append(Paragraph(
                "Não foi possível obter notícias recentes sobre SRAG no momento da geração do relatório.",
                self.styles['TextoNormal']
            ))
            return

        elements.append(Paragraph(
            f"Foram identificadas <b>{len(noticias)}</b> notícias recentes relacionadas à SRAG. "
            "A tabela abaixo apresenta as principais manchetes encontradas:",
            self.styles['TextoNormal']
        ))
        elements.append(Spacer(1, 15))

        dados_tabela = [['#', 'Título', 'Fonte']]
        for i, noticia in enumerate(noticias[:5], 1):
            titulo = noticia.get('titulo', 'Sem título')
            if len(titulo) > 70:
                titulo = titulo[:67] + '...'
            fonte = noticia.get('fonte', 'N/A')
            if len(fonte) > 20:
                fonte = fonte[:17] + '...'
            dados_tabela.append([str(i), titulo, fonte])

        tabela = Table(dados_tabela, colWidths=[1 * cm, 12.5 * cm, 3.5 * cm])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(tabela)
        elements.append(Spacer(1, 15))

        elements.append(Paragraph(
            "<i>Nota: A análise detalhada destas notícias, incluindo resumos e correlação com os dados "
            "epidemiológicos, está apresentada na próxima seção (Análise do Agente de IA).</i>",
            self.styles['TextoNormal']
        ))

    def _criar_secao_conclusao(self, elements: List, metricas: Dict[str, Any]):
        elements.append(Paragraph("6. Conclusões e Recomendações", self.styles['Secao']))

        taxa_mortalidade = metricas.get('taxa_mortalidade')
        taxa_uti = metricas.get('taxa_ocupacao_uti')
        taxa_aumento = metricas.get('taxa_aumento_casos')

        conclusoes = []

        if taxa_mortalidade and taxa_mortalidade.valor > 5:
            conclusoes.append(
                "A taxa de mortalidade está elevada, indicando necessidade de atenção especial aos casos graves.")

        if taxa_uti and taxa_uti.valor > 20:
            conclusoes.append("A alta taxa de ocupação de UTI sugere pressão significativa sobre o sistema de saúde.")

        if taxa_aumento and taxa_aumento.valor > 10:
            conclusoes.append("O aumento expressivo de casos indica possível agravamento do cenário epidemiológico.")
        elif taxa_aumento and taxa_aumento.valor < -10:
            conclusoes.append("A redução de casos sugere melhora no cenário epidemiológico.")

        if not conclusoes:
            conclusoes.append("Os indicadores analisados estão dentro de parâmetros esperados para o período.")

        elements.append(Paragraph("<b>Conclusões:</b>", self.styles['TextoNormal']))
        for conclusao in conclusoes:
            elements.append(Paragraph(f"• {conclusao}", self.styles['TextoNormal']))

        elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>Recomendações:</b>", self.styles['TextoNormal']))
        recomendacoes = [
            "Manter vigilância epidemiológica ativa e monitoramento contínuo dos indicadores.",
            "Fortalecer campanhas de vacinação contra influenza e COVID-19.",
            "Garantir disponibilidade de leitos de UTI e equipamentos de suporte ventilatório.",
            "Promover medidas de prevenção junto à população, especialmente grupos de risco."
        ]

        for rec in recomendacoes:
            elements.append(Paragraph(f"• {rec}", self.styles['TextoNormal']))

    def _criar_rodape(self, elements: List):

        elements.append(Spacer(1, 30))
        elements.append(Table(
            [['']],
            colWidths=[17 * cm],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, -1), 1, colors.gray)
            ])
        ))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(
            f"Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Rodape']
        ))
        elements.append(Paragraph(
            "Dados: SIVEP-Gripe/DATASUS | Sistema SRAG Health Report",
            self.styles['Rodape']
        ))

    def gerar_relatorio(self,
                        noticias: List[Dict] = None,
                        analise_llm: str = None) -> str:

        logger.info("Iniciando geração do relatório PDF...")

        logger.info("Coletando métricas...")
        metricas = self.metrics.calcular_todas_metricas()

        logger.info("Coletando estatísticas...")
        stats = self.db.obter_estatisticas_gerais()

        logger.info("Gerando gráficos...")
        graficos = self.charts.gerar_todos_graficos()

        if noticias is None:
            logger.info("Buscando notícias...")
            try:
                from tools.news_tool import NewsTool
                news_tool = NewsTool()
                dados_noticias = news_tool.obter_noticias_para_relatorio(max_noticias=5)
                noticias = dados_noticias.get('noticias', [])
                logger.info(f"Encontradas {len(noticias)} notícias")
            except Exception as e:
                logger.warning(f"Não foi possível buscar notícias: {e}")
                noticias = []

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_srag_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        self._criar_cabecalho(elements)
        self._criar_resumo_executivo(elements, metricas, stats)
        self._criar_secao_metricas(elements, metricas)
        self._criar_secao_graficos(elements, graficos)

        self._criar_secao_noticias(elements, noticias)

        if analise_llm:
            elements.append(PageBreak())
            elements.append(Paragraph("5. Análise do Agente de IA", self.styles['Secao']))

            elements.append(Paragraph(
                "A seguir, apresentamos a análise elaborada pelo agente de IA com base nas notícias "
                "coletadas e nos dados epidemiológicos:",
                self.styles['TextoNormal']
            ))
            elements.append(Spacer(1, 10))

            paragrafos = analise_llm.split('\n')
            for p in paragrafos:
                if p.strip():

                    p_limpo = p.strip()
                    if p_limpo.startswith('**') and p_limpo.endswith('**'):

                        titulo = p_limpo.replace('**', '')
                        elements.append(Spacer(1, 8))
                        elements.append(Paragraph(f"<b>{titulo}</b>", self.styles['TextoNormal']))
                    elif p_limpo.startswith('#'):

                        titulo = p_limpo.lstrip('#').strip()
                        elements.append(Spacer(1, 8))
                        elements.append(Paragraph(f"<b>{titulo}</b>", self.styles['TextoNormal']))
                    else:
                        elements.append(Paragraph(p_limpo, self.styles['TextoNormal']))
                    elements.append(Spacer(1, 3))

        self._criar_secao_conclusao(elements, metricas)
        self._criar_rodape(elements)


        logger.info(f"Salvando PDF em: {filepath}")
        doc.build(elements)

        logger.info("Relatório PDF gerado com sucesso!")
        return filepath


def criar_report_tool(output_dir: str = None) -> ReportTool:

    return ReportTool(output_dir)


def tool_gerar_relatorio_pdf(noticias: List[Dict] = None) -> str:

    try:
        report = ReportTool()
        caminho = report.gerar_relatorio(noticias=noticias)
        return f"Relatório PDF gerado com sucesso: {caminho}"
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}"


if __name__ == "__main__":

    try:

        report = ReportTool()
        caminho = report.gerar_relatorio()

        print(f"Arquivo: {caminho}")

    except Exception as e:
        print(f"\n Erro: {e}")
        import traceback

        traceback.print_exc()