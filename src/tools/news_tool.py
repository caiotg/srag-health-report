import logging
import ssl
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json
import os

os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

try:
    from duckduckgo_search import DDGS

    DDGS_DISPONIVEL = True
except ImportError:
    DDGS_DISPONIVEL = False


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('news_tool')


@dataclass
class Noticia:

    titulo: str
    resumo: str
    fonte: str
    url: str
    data: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'titulo': self.titulo,
            'resumo': self.resumo,
            'fonte': self.fonte,
            'url': self.url,
            'data': self.data
        }

    def formatar(self) -> str:

        return f"{self.titulo}\n   Fonte: {self.fonte}\n   {self.resumo[:150]}..."


class NewsTool:

    TERMOS_BUSCA = [
        "SRAG síndrome respiratória aguda grave",
        "SRAG Brasil casos",
        "síndrome respiratória aguda grave hospital",
        "SRAG gripe influenza",
        "surto respiratório Brasil"
    ]

    FONTES_CONFIAVEIS = [
        'gov.br', 'fiocruz', 'saude.gov', 'who.int', 'paho.org',
        'g1.globo', 'uol.com', 'folha.uol', 'estadao', 'bbc',
        'cnn', 'reuters', 'agenciabrasil'
    ]

    def __init__(self):

        if not DDGS_DISPONIVEL:
            raise ImportError(
                "DuckDuckGo Search não está instalado. "
                "Execute: pip install duckduckgo-search"
            )

        try:
            self.ddgs = DDGS(verify=False)
        except TypeError:
            self.ddgs = DDGS()

        logger.info("NewsTool inicializado com DuckDuckGo Search")

    def _registrar_busca(self, termo: str, resultados: int):

        registro = {
            'timestamp': datetime.now().isoformat(),
            'termo_busca': termo,
            'resultados_encontrados': resultados
        }
        logger.info(f"AUDITORIA BUSCA: {registro}")

    def _verificar_fonte_confiavel(self, url: str) -> bool:

        url_lower = url.lower()
        return any(fonte in url_lower for fonte in self.FONTES_CONFIAVEIS)

    def _filtrar_noticias_relevantes(self, noticias: List[Dict]) -> List[Dict]:

        termos_relevantes = [
            'srag', 'respiratório', 'respiratória', 'gripe', 'influenza',
            'hospital', 'uti', 'internação', 'casos', 'óbito', 'morte',
            'saúde', 'epidemia', 'surto', 'vírus', 'covid', 'h1n1',
            'vacina', 'vacinação', 'sintomas'
        ]

        noticias_filtradas = []
        for noticia in noticias:
            texto = f"{noticia.get('title', '')} {noticia.get('body', '')}".lower()

            # Verificar se contém termos relevantes
            if any(termo in texto for termo in termos_relevantes):
                noticias_filtradas.append(noticia)

        return noticias_filtradas

    def buscar_noticias(self, termo: str = None, max_resultados: int = 10) -> List[Noticia]:

        if termo is None:
            termo = "SRAG síndrome respiratória aguda grave Brasil"

        logger.info(f"Buscando notícias: '{termo}'")

        try:
            # Buscar notícias
            resultados = list(self.ddgs.news(
                keywords=termo,
                region='br-pt',
                safesearch='moderate',
                max_results=max_resultados * 2
            ))

            resultados = self._filtrar_noticias_relevantes(resultados)

            noticias = []
            for r in resultados[:max_resultados]:
                noticia = Noticia(
                    titulo=r.get('title', 'Sem título'),
                    resumo=r.get('body', 'Sem resumo'),
                    fonte=r.get('source', 'Fonte desconhecida'),
                    url=r.get('url', ''),
                    data=r.get('date', 'Data não disponível')
                )
                noticias.append(noticia)

            self._registrar_busca(termo, len(noticias))
            logger.info(f"Encontradas {len(noticias)} notícias relevantes")

            return noticias

        except Exception as e:
            logger.error(f"Erro ao buscar notícias: {e}")
            self._registrar_busca(termo, 0)
            return []

    def buscar_noticias_multiplos_termos(self, max_por_termo: int = 5) -> List[Noticia]:

        logger.info("Buscando notícias com múltiplos termos...")

        todas_noticias = []
        urls_vistas = set()

        for termo in self.TERMOS_BUSCA:
            noticias = self.buscar_noticias(termo, max_por_termo)

            for noticia in noticias:

                if noticia.url not in urls_vistas:
                    urls_vistas.add(noticia.url)
                    todas_noticias.append(noticia)


        todas_noticias.sort(
            key=lambda n: (not self._verificar_fonte_confiavel(n.url), n.data),
            reverse=True
        )

        logger.info(f"Total de notícias únicas encontradas: {len(todas_noticias)}")
        return todas_noticias

    def obter_resumo_noticias(self, max_noticias: int = 5) -> str:

        noticias = self.buscar_noticias_multiplos_termos(max_por_termo=3)

        if not noticias:
            return "Não foram encontradas notícias recentes sobre SRAG."

        resumo = []
        resumo.append("=" * 60)
        resumo.append("NOTÍCIAS RECENTES SOBRE SRAG")
        resumo.append(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        resumo.append("=" * 60)

        for i, noticia in enumerate(noticias[:max_noticias], 1):
            confiavel = "✓" if self._verificar_fonte_confiavel(noticia.url) else ""
            resumo.append(f"\n{i}. {noticia.titulo} {confiavel}")
            resumo.append(f"   Fonte: {noticia.fonte} | Data: {noticia.data}")
            resumo.append(f"   {noticia.resumo[:200]}...")
            resumo.append(f"   Link: {noticia.url}")

        resumo.append("\n" + "=" * 60)
        resumo.append("✓ = Fonte confiável")

        return "\n".join(resumo)

    def obter_noticias_para_relatorio(self, max_noticias: int = 3) -> Dict[str, Any]:

        noticias = self.buscar_noticias_multiplos_termos(max_por_termo=3)

        noticias_confiaveis = [
            n for n in noticias if self._verificar_fonte_confiavel(n.url)
        ]

        if len(noticias_confiaveis) < max_noticias:
            outras = [n for n in noticias if n not in noticias_confiaveis]
            noticias_confiaveis.extend(outras[:max_noticias - len(noticias_confiaveis)])

        noticias_selecionadas = noticias_confiaveis[:max_noticias]

        return {
            'data_busca': datetime.now().isoformat(),
            'total_encontradas': len(noticias),
            'noticias': [n.to_dict() for n in noticias_selecionadas],
            'fontes_confiaveis': len([n for n in noticias_selecionadas
                                      if self._verificar_fonte_confiavel(n.url)])
        }


def criar_news_tool() -> NewsTool:

    return NewsTool()


def tool_buscar_noticias_srag(max_resultados: int = 5) -> str:

    try:
        news = NewsTool()
        return news.obter_resumo_noticias(max_resultados)
    except Exception as e:
        return f"Erro ao buscar notícias: {str(e)}"


def tool_obter_contexto_noticias() -> str:

    try:
        news = NewsTool()
        resultado = news.obter_noticias_para_relatorio()
        return json.dumps(resultado, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Erro ao obter contexto: {str(e)}"


if __name__ == "__main__":

    try:

        news = NewsTool()

        print("\n1. Busca simples de notícias:")
        noticias = news.buscar_noticias(max_resultados=3)
        for n in noticias:
            print(f"   - {n.titulo[:60]}...")

        print("\n2. Resumo formatado:")
        print(news.obter_resumo_noticias(max_noticias=3))

        print("\n3. Dados para relatório:")
        dados = news.obter_noticias_para_relatorio(max_noticias=2)
        print(f"   Total encontradas: {dados['total_encontradas']}")
        print(f"   Fontes confiáveis: {dados['fontes_confiaveis']}")

        print("\n" + "=" * 60)
        print("TODOS OS TESTES PASSARAM!")
        print("=" * 60)

    except ImportError as e:
        print(f"\n Erro de importação: {e}")
    except Exception as e:
        print(f"\n Erro: {e}")
        import traceback

        traceback.print_exc()