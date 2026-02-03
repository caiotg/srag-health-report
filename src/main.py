"""
SRAG Health Report - Sistema de Agentes para Geração de Relatórios
"""
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def main():
    """Função principal do sistema."""
    print("=" * 50)
    print("SRAG Health Report - Sistema Iniciado")
    print("=" * 50)

    # TODO: Implementar fluxo do agente
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️  GROQ_API_KEY não configurada no .env")
        return

    print("✅ Configuração carregada com sucesso!")
    print("✅ Pronto para processar dados...")


if __name__ == "__main__":
    main()