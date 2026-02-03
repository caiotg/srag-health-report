import os
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('primp').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('database_tool').setLevel(logging.WARNING)
logging.getLogger('metrics_tool').setLevel(logging.WARNING)
logging.getLogger('charts_tool').setLevel(logging.WARNING)
logging.getLogger('news_tool').setLevel(logging.WARNING)
logging.getLogger('report_tool').setLevel(logging.WARNING)
logging.getLogger('orquestrador').setLevel(logging.WARNING)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orquestrador import AgenteOrquestrador


def banner():

    print("""
    HEALTH REPORT - Sistema de Relatórios SRAG
    Powered by AI Agents
    """)

def verificar_configuracao():

    print("\nVerificando configuração...")

    erros = []

    if not os.getenv("GROQ_API_KEY"):
        erros.append("GROQ_API_KEY não configurada no .env")

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'processed', 'srag.db'
    )

    if not os.path.exists(db_path):
        erros.append(f"Banco de dados não encontrado: {db_path}")

    if erros:
        print("\nErros de configuração:")
        for erro in erros:
            print(f"  - {erro}")
        return False
    return True


def gerar_relatorio():
    print("\nInicializando agente orquestrador...")

    try:
        agente = AgenteOrquestrador()
        print("Agente inicializado!")

        print("\nGerando relatório completo...")
        print("   Aguarde, isso pode levar alguns segundos...\n")

        resultado = agente.gerar_relatorio_completo()

        if resultado["sucesso"]:
            print("\n" + "=" * 60)
            print("RELATÓRIO GERADO COM SUCESSO!")
            print("=" * 60)
            print(f"\n{resultado['resposta']}")

        else:
            print(f"\nErro ao gerar relatório: {resultado['erro']}")

    except Exception as e:
        print(f"\nErro: {e}")


def modo_interativo():

    print("\nModo Interativo")
    print("Digite suas perguntas sobre SRAG ou 'sair' para encerrar.\n")

    agente = AgenteOrquestrador()

    while True:
        try:
            pergunta = input("\nVocê: ").strip()

            if pergunta.lower() in ['sair', 'exit', 'quit', 'q']:
                print("\nAté logo!")
                break

            if not pergunta:
                continue

            print("\nAgente está processando...")
            resultado = agente.executar(pergunta)

            if resultado["sucesso"]:
                print(f"\nAgente: {resultado['resposta']}")
            else:
                print(f"\nErro: {resultado['erro']}")

        except KeyboardInterrupt:
            print("\n\nAté logo!")
            break


def main():

    parser = argparse.ArgumentParser(
        description='SRAG Health Report - Sistema de Relatórios com IA'
    )
    parser.add_argument(
        '--modo', '-m',
        choices=['relatorio', 'interativo', 'verificar'],
        default='relatorio',
        help='Modo de execução (padrão: relatorio)'
    )

    args = parser.parse_args()

    banner()

    if not verificar_configuracao():
        print("\nCorrija os erros de configuração antes de continuar.")
        sys.exit(1)

    if args.modo == 'verificar':
        print("\nSistema configurado corretamente!")

    elif args.modo == 'relatorio':
        gerar_relatorio()

    elif args.modo == 'interativo':
        modo_interativo()


if __name__ == "__main__":
    main()