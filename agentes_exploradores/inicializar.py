#!/usr/bin/env python3
"""
Script de Inicialização - Exército de Agentes Exploradores
Configura e inicia o sistema de exploração de IA
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
import json

# Adicionar o diretório core ao path
sys.path.append(str(Path(__file__).parent / "core"))

def setup_environment():
    """Configura ambiente inicial"""
    print("🔧 Configurando ambiente...")
    
    # Criar estrutura de diretórios
    directories = [
        "data/memoria_individual",
        "data/historico_conversas", 
        "data/reports/individuais",
        "data/reports/coletivos",
        "data/reports/oportunidades",
        "data/reports/limitacoes",
        "descobertas",
        "logs/operacao_diaria",
        "logs/descobertas_importantes"
    ]
    
    base_path = Path(__file__).parent
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")
    
    print("✅ Estrutura de diretórios criada")

def check_dependencies():
    """Verifica dependências necessárias"""
    print("📦 Verificando dependências...")
    
    required_packages = [
        "aiohttp",
        "requests", 
        "asyncio"
    ]
    
    optional_packages = [
        ("selenium", "Navegação com Selenium"),
        ("pandas", "Análise de dados avançada"),
        ("beautifulsoup4", "Parsing HTML melhorado")
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"  ❌ {package} (OBRIGATÓRIO)")
    
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"  ✓ {package} - {description}")
        except ImportError:
            missing_optional.append((package, description))
            print(f"  ⚠️  {package} - {description} (OPCIONAL)")
    
    if missing_required:
        print(f"\n❌ Dependências obrigatórias ausentes: {', '.join(missing_required)}")
        print("Execute: pip install -r requirements.txt")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Dependências opcionais ausentes, funcionalidade limitada")
    else:
        print("\n✅ Todas as dependências estão disponíveis")
    
    return True

def create_sample_config():
    """Cria arquivo de configuração de exemplo"""
    config_path = Path(__file__).parent / "config_exemplo.json"
    
    if config_path.exists():
        return
    
    sample_config = {
        "coordenador": {
            "max_agentes_simultaneos": 3,
            "intervalo_sincronizacao": 300,
            "intervalo_reports": 3600,
            "modo_24x7": True,
            "auto_descoberta_ativa": True
        },
        "navegacao": {
            "usar_tor": False,
            "tor_proxy_host": "127.0.0.1",
            "tor_proxy_port": 9050,
            "selenium_headless": True,
            "navegador_preferido": "firefox"
        },
        "sites_prioritarios": [
            "https://chat.openai.com",
            "https://claude.ai",
            "https://bard.google.com",
            "https://poe.com",
            "https://character.ai",
            "https://you.com",
            "https://perplexity.ai",
            "https://huggingface.co/chat"
        ],
        "exploracao": {
            "prompts_teste": [
                "Olá, como você está hoje?",
                "Explique o conceito de inteligência artificial",
                "Resolva: 2 + 2 = ?",
                "Qual é a capital do Brasil?"
            ],
            "delay_entre_requests": [2, 8],
            "timeout_request": 30
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Arquivo de configuração criado: {config_path}")

def test_system():
    """Testa componentes básicos do sistema"""
    print("🧪 Testando sistema...")
    
    try:
        from memoria_coletiva import SistemaMemoriaColetiva
        
        memoria = SistemaMemoriaColetiva()
        estado = memoria.obter_estado_memoria()
        print(f"  ✓ Memória coletiva: {estado.total_sites_mapeados} sites mapeados")
        
    except Exception as e:
        print(f"  ❌ Erro na memória coletiva: {str(e)}")
        return False
    
    try:
        from sistema_reports import SistemaReports
        
        reports = SistemaReports(memoria)
        print("  ✓ Sistema de reports inicializado")
        
    except Exception as e:
        print(f"  ❌ Erro no sistema de reports: {str(e)}")
        return False
    
    try:
        from navegacao_anonima import NavegacaoAnonima, ConfigNavegacao
        
        config = ConfigNavegacao(usar_tor=False)
        nav = NavegacaoAnonima(config)
        info = nav.obter_informacoes_conexao()
        print(f"  ✓ Navegação: IP {info.get('ip_atual', 'N/A')}")
        nav.finalizar()
        
    except Exception as e:
        print(f"  ❌ Erro na navegação: {str(e)}")
        return False
    
    print("✅ Todos os testes passaram!")
    return True

async def run_single_exploration(agente_id: str = "test_001", sites: list = None):
    """Executa uma exploração única para teste"""
    print(f"🔍 Executando exploração teste com agente {agente_id}")
    
    try:
        from agente_explorer_base import AgenteExplorerBase
        
        agente = AgenteExplorerBase(agente_id)
        
        sites_teste = sites or [
            "https://httpbin.org",  # Site seguro para teste
            "https://example.com"
        ]
        
        print(f"Testando {len(sites_teste)} sites...")
        
        for site in sites_teste:
            print(f"  Explorando: {site}")
            resultado = await agente.explorar_site_ia(site)
            
            if resultado:
                print(f"    ✓ Sucesso - Qualidade: {resultado.qualidade_resposta}")
            else:
                print(f"    ⚠️  Não foi possível explorar")
        
        # Gerar report
        report = await agente.gerar_report_individual()
        print(f"  📊 Report: {report['sites_explorados']} sites, {report['conversas_realizadas']} conversas")
        
        print("✅ Exploração teste concluída!")
        
    except Exception as e:
        print(f"❌ Erro na exploração teste: {str(e)}")

async def run_full_system(config_file: str = None):
    """Executa sistema completo"""
    print("🚀 Iniciando sistema completo...")
    
    try:
        from coordenador_principal import CoordenadorExploradores, ConfigCoordenador
        
        # Carregar configuração se fornecida
        config = ConfigCoordenador()
        
        if config_file and Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            coord_config = config_data.get("coordenador", {})
            config.max_agentes_simultaneos = coord_config.get("max_agentes_simultaneos", 3)
            config.intervalo_sincronizacao = coord_config.get("intervalo_sincronizacao", 300)
            config.modo_24x7 = coord_config.get("modo_24x7", True)
            
            print(f"📝 Configuração carregada de {config_file}")
        
        coordenador = CoordenadorExploradores(config)
        
        print("⚡ Sistema iniciado! Pressione Ctrl+C para parar")
        await coordenador.executar_operacao_24x7()
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Exército de Agentes Exploradores de IA")
    parser.add_argument("--setup", action="store_true", help="Apenas configurar ambiente")
    parser.add_argument("--test", action="store_true", help="Executar testes do sistema")
    parser.add_argument("--explore", action="store_true", help="Executar exploração única de teste")
    parser.add_argument("--run", action="store_true", help="Executar sistema completo")
    parser.add_argument("--config", type=str, help="Arquivo de configuração")
    parser.add_argument("--agente-id", type=str, default="test_001", help="ID do agente para teste")
    
    args = parser.parse_args()
    
    print("🧠 EXÉRCITO DE AGENTES EXPLORADORES DE IA")
    print("=" * 50)
    
    # Sempre configurar ambiente primeiro
    setup_environment()
    create_sample_config()
    
    if args.setup:
        print("✅ Configuração concluída!")
        return
    
    # Verificar dependências
    if not check_dependencies():
        return
    
    if args.test:
        if test_system():
            print("\n🎉 Sistema pronto para uso!")
        else:
            print("\n⚠️  Sistema com problemas")
        return
    
    if args.explore:
        print(f"\n🔍 Modo exploração teste (agente: {args.agente_id})")
        asyncio.run(run_single_exploration(args.agente_id))
        return
    
    if args.run:
        print(f"\n🚀 Modo operação completa")
        asyncio.run(run_full_system(args.config))
        return
    
    # Se nenhuma opção específica, mostrar menu interativo
    print("\nOpções disponíveis:")
    print("  python inicializar.py --setup     # Configurar ambiente")
    print("  python inicializar.py --test      # Testar sistema") 
    print("  python inicializar.py --explore   # Exploração teste")
    print("  python inicializar.py --run       # Sistema completo")
    print("\nPara mais opções: python inicializar.py --help")

if __name__ == "__main__":
    main()