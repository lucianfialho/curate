#!/usr/bin/env python3
"""
AIlert Sentiment API Consumer

Este script consome a API de curadoria de conteúdo AIlert Sentiment para buscar
notícias, papers de pesquisa e repositórios relevantes sobre tópicos específicos.
"""

import argparse
import json
import sys
import requests
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações padrão
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_MAX_NEWS = 10
DEFAULT_MAX_PAPERS = 5
DEFAULT_MAX_REPOS = 5


def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Consulta a AIlert Sentiment API para curadoria de conteúdo.')
    
    parser.add_argument('-u', '--url', type=str, default=DEFAULT_API_URL,
                        help=f'URL base da API (default: {DEFAULT_API_URL})')
    
    parser.add_argument('-n', '--max-news', type=int, default=DEFAULT_MAX_NEWS,
                        help=f'Número máximo de notícias (default: {DEFAULT_MAX_NEWS})')
    
    parser.add_argument('-p', '--max-papers', type=int, default=DEFAULT_MAX_PAPERS,
                        help=f'Número máximo de papers (default: {DEFAULT_MAX_PAPERS})')
    
    parser.add_argument('-r', '--max-repos', type=int, default=DEFAULT_MAX_REPOS,
                        help=f'Número máximo de repositórios (default: {DEFAULT_MAX_REPOS})')
    
    parser.add_argument('-k', '--keywords', type=str, nargs='+',
                        help='Palavras-chave para filtrar conteúdo (ex: AI "machine learning" robotics)')
    
    parser.add_argument('-s', '--sentiment', action='store_true',
                        help='Incluir análise de sentimento nos resultados')
    
    parser.add_argument('-o', '--output', type=str,
                        help='Arquivo para salvar resultados em JSON (opcional)')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Exibir informações detalhadas durante a execução')
    
    return parser.parse_args()


def build_request(args) -> Dict[str, Any]:
    """
    Constrói o corpo da requisição para a API com base nos argumentos.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        Dicionário com parâmetros da requisição
    """
    request = {
        "max_news": args.max_news,
        "max_papers": args.max_papers,
        "max_repos": args.max_repos,
        "include_sentiment": args.sentiment,
        "metadata": {
            "source": "curate.py",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    if args.keywords:
        # Garante que as palavras-chave não estejam vazias
        request["keywords"] = [k for k in args.keywords if k.strip()]
    
    return request


def call_api(url: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faz uma chamada para a API de curadoria.
    
    Args:
        url: URL da API
        request_data: Dados da requisição
        
    Returns:
        Resposta da API em formato de dicionário
        
    Raises:
        Exception: Se houver erro na chamada da API
    """
    api_url = f"{url.rstrip('/')}/api/curate"
    
    try:
        logger.info(f"Enviando requisição para {api_url}")
        
        response = requests.post(
            api_url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # Timeout generoso para permitir processamento de sentimento
        )
        
        # Verifica se a requisição foi bem-sucedida
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP: {e}")
        if e.response is not None:
            logger.error(f"Detalhes: {e.response.text}")
        raise
    
    except requests.exceptions.ConnectionError:
        logger.error(f"Erro de conexão: Não foi possível conectar a {api_url}")
        logger.error("Verifique se o servidor está em execução e acessível.")
        raise
    
    except requests.exceptions.Timeout:
        logger.error("Timeout: A requisição excedeu o tempo limite.")
        raise
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        raise
    
    except json.JSONDecodeError:
        logger.error("Erro ao decodificar resposta JSON.")
        raise
    
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise


def print_summary(result: Dict[str, Any], verbose: bool = False):
    """
    Imprime um resumo do conteúdo curado.
    
    Args:
        result: Resposta da API
        verbose: Se True, imprime informações detalhadas
    """
    if not result:
        logger.error("Resposta vazia da API")
        return
    
    if isinstance(result, str):
        logger.error(f"Erro na resposta: {result}")
        return
    
    if "error" in result:
        logger.error(f"Erro na resposta: {result['error']}")
        return
    
    content = result.get("content", {})
    insights = result.get("insights", {})
    
    if not content:
        logger.error("Conteúdo não encontrado na resposta")
        if verbose:
            logger.debug(f"Resposta completa: {json.dumps(result, indent=2)}")
        return
    
    # Extrai conteúdo
    news = content.get("news", [])
    papers = content.get("papers", [])
    repos = content.get("repos", [])
    
    # Imprime cabeçalho
    print("\n" + "="*80)
    print(f"  AIlert Sentiment - Resultados da Curadoria ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*80)
    
    # Resumo geral
    print(f"\nTotal de itens encontrados: {len(news) + len(papers) + len(repos)}")
    print(f"  - Notícias: {len(news)}")
    print(f"  - Papers de pesquisa: {len(papers)}")
    print(f"  - Repositórios: {len(repos)}")
    
    # Imprime análise de sentimento se disponível
    if insights:
        print("\nAnálise de Sentimento:")
        if "overall_sentiment" in insights:
            sentiment = insights["overall_sentiment"]
            print(f"  - Sentimento geral: {sentiment}")
        
        if "topic_insights" in insights:
            print("  - Insights por tópico:")
            for topic, data in insights["topic_insights"].items():
                print(f"    * {topic}: {data.get('sentiment', 'N/A')}")
    
    # Imprime notícias
    if news:
        print("\nNotícias em Destaque:")
        for i, item in enumerate(news[:5], 1):  # Limita a 5 para não sobrecarregar o terminal
            title = item.get('title', 'Sem título')
            primary_source = item.get('primary_source', 'Fonte desconhecida')
            primary_link = item.get('primary_link', '#')
            source_count = item.get('source_count', 0)
            
            print(f"  {i}. {title}")
            print(f"     Fonte: {primary_source} ({source_count} fontes)")
            print(f"     Link: {primary_link}")
            
            # Informações de sentimento para o item
            sentiment_analysis = item.get("sentiment_analysis", {})
            if sentiment_analysis and isinstance(sentiment_analysis, dict):
                sentiment = sentiment_analysis.get("overall_sentiment", "N/A")
                print(f"     Sentimento: {sentiment}")
            
            print()
    
    # Imprime papers
    if papers:
        print("\nPapers de Pesquisa Relevantes:")
        for i, paper in enumerate(papers[:3], 1):  # Limita a 3
            title = paper.get('title', 'Sem título')
            authors = paper.get('authors', [])
            link = paper.get('link', '#')
            
            print(f"  {i}. {title}")
            if authors:
                print(f"     Autores: {', '.join(authors[:3])}" + 
                      (f" e outros {len(authors)-3}" if len(authors) > 3 else ""))
            print(f"     Link: {link}")
            print()
    
    # Imprime repos
    if repos:
        print("\nRepositórios em Destaque:")
        for i, repo in enumerate(repos[:3], 1):  # Limita a 3
            name = repo.get('name', 'Sem nome')
            summary = repo.get('summary', 'Sem descrição')
            link = repo.get('link', '#')
            
            print(f"  {i}. {name}")
            print(f"     Descrição: {summary[:100]}..." if len(summary) > 100 else f"     Descrição: {summary}")
            print(f"     Link: {link}")
            print()
    
    # Se verbose, imprime detalhes adicionais
    if verbose:
        print("\nDetalhes Adicionais:")
        print(f"  - Timestamp: {content.get('timestamp', 'N/A')}")
        print(f"  - Versão: {content.get('version', 'N/A')}")
        
        if "metadata" in content and content["metadata"]:
            print("  - Metadata:")
            for key, value in content["metadata"].items():
                print(f"    * {key}: {value}")
    
    print("\n" + "="*80)


def save_to_file(data: Dict[str, Any], filename: str):
    """
    Salva os resultados em um arquivo JSON.
    
    Args:
        data: Dados a serem salvos
        filename: Nome do arquivo
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Resultados salvos em {filename}")
    except Exception as e:
        logger.error(f"Erro ao salvar resultados: {e}")


def debug_response(response):
    """
    Imprime informações de depuração sobre a resposta.
    
    Args:
        response: Resposta a ser analisada
    """
    print("\n--- INFORMAÇÕES DE DEPURAÇÃO ---")
    print(f"Tipo da resposta: {type(response)}")
    
    if isinstance(response, dict):
        print("Chaves da resposta:", list(response.keys()))
        
        content = response.get('content')
        if content:
            print("Tipo do content:", type(content))
            if isinstance(content, dict):
                print("Chaves do content:", list(content.keys()))
    
    print(f"Conteúdo completo: {json.dumps(response, default=str, indent=2)}")
    print("--- FIM DA DEPURAÇÃO ---\n")


def main():
    """Função principal do script."""
    args = parse_arguments()
    
    # Configura log verboso se solicitado
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Constrói requisição
        request_data = build_request(args)
        
        if args.verbose:
            logger.debug(f"Requisição: {json.dumps(request_data, indent=2)}")
        
        # Chama a API
        result = call_api(args.url, request_data)
        
        # Se estiver no modo verbose, mostra informações de depuração
        if args.verbose:
            debug_response(result)
        
        # Imprime resumo
        print_summary(result, args.verbose)
        
        # Salva em arquivo se solicitado
        if args.output:
            save_to_file(result, args.output)
        
        return 0
    
    except Exception as e:
        logger.error(f"Erro: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())