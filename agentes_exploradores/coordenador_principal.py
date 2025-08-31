#!/usr/bin/env python3
"""
Coordenador Principal - Exército de Agentes Exploradores de IA
Orquestra a operação de múltiplos agentes exploradores 24/7
"""

import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import concurrent.futures

# Imports dos módulos principais
from agente_explorer_base import AgenteExplorerBase
from memoria_coletiva import SistemaMemoriaColetiva
from sistema_reports import SistemaReports
from navegacao_anonima import NavegacaoAnonima, ConfigNavegacao, DetectorInterfaceChat

@dataclass
class ConfigCoordenador:
    """Configurações do coordenador principal"""
    max_agentes_simultaneos: int = 5
    intervalo_sincronizacao: int = 300  # 5 minutos
    intervalo_reports: int = 3600  # 1 hora
    sites_prioritarios_base: List[str] = None
    modo_24x7: bool = True
    auto_descoberta_ativa: bool = True
    max_tentativas_erro: int = 3
    pausa_entre_ciclos: int = 60  # segundos

class CoordenadorExploradores:
    """Coordenador principal dos agentes exploradores"""
    
    def __init__(self, config: ConfigCoordenador = None):
        self.config = config or ConfigCoordenador()
        self.logger = self._setup_logging()
        
        # Sistemas principais
        self.memoria_coletiva = SistemaMemoriaColetiva()
        self.sistema_reports = SistemaReports(self.memoria_coletiva)
        
        # Controle de agentes
        self.agentes_ativos: Dict[str, AgenteExplorerBase] = {}
        self.tasks_agentes: Dict[str, asyncio.Task] = {}
        self.shutdown_event = asyncio.Event()
        
        # Configurar sites prioritários base
        if not self.config.sites_prioritarios_base:
            self.config.sites_prioritarios_base = [
                "https://chat.openai.com",
                "https://claude.ai",
                "https://bard.google.com",
                "https://poe.com",
                "https://character.ai",
                "https://you.com",
                "https://perplexity.ai",
                "https://huggingface.co/chat",
                "http://localhost:11434",  # Ollama local
                "http://localhost:7860",  # Gradio comum
            ]
            
        # Estatísticas operacionais
        self.stats = {
            "inicio_operacao": datetime.now().isoformat(),
            "total_ciclos_executados": 0,
            "total_sites_descobertos": 0,
            "total_erros": 0,
            "ultima_sincronizacao": None,
            "ultimo_report": None
        }
        
        # Configurar handlers de sinal para shutdown graceful
        self._configurar_shutdown_handlers()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging principal"""
        logger = logging.getLogger("coordenador_exploradores")
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        log_path = Path("../logs/coordenador_principal.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
        
    def _configurar_shutdown_handlers(self):
        """Configura handlers para shutdown graceful"""
        def signal_handler(signum, frame):
            self.logger.info(f"Sinal recebido: {signum}. Iniciando shutdown...")
            self.shutdown_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def inicializar_agente(self, agente_id: str) -> AgenteExplorerBase:
        """Inicializa um novo agente explorador"""
        try:
            self.logger.info(f"Inicializando agente {agente_id}")
            
            agente = AgenteExplorerBase(agente_id)
            
            # Sincronizar com memória coletiva
            dados_sincronizacao = self.memoria_coletiva.sincronizar_agente(agente_id)
            
            self.agentes_ativos[agente_id] = agente
            
            self.logger.info(f"Agente {agente_id} inicializado com sucesso")
            return agente
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar agente {agente_id}: {str(e)}")
            raise
            
    async def executar_ciclo_agente(self, agente_id: str):
        """Executa ciclo contínuo de exploração para um agente"""
        tentativas_erro = 0
        
        while not self.shutdown_event.is_set():
            try:
                agente = self.agentes_ativos.get(agente_id)
                if not agente:
                    agente = await self.inicializar_agente(agente_id)
                    
                # Obter sites prioritários atualizados
                sites_alvo = self.memoria_coletiva.obter_sites_prioritarios(agente_id, limite=10)
                
                # Se não há sites prioritários, usar lista base
                if not sites_alvo:
                    sites_alvo = self.config.sites_prioritarios_base[:5]
                    
                self.logger.info(f"Agente {agente_id} iniciando exploração de {len(sites_alvo)} sites")
                
                # Executar ciclo de exploração
                await agente.executar_ciclo_exploracao(sites_alvo)
                
                # Atualizar estatísticas
                self.stats["total_ciclos_executados"] += 1
                tentativas_erro = 0  # Reset contador de erros
                
                # Auto-descoberta de novos sites
                if self.config.auto_descoberta_ativa:
                    await self._executar_auto_descoberta(agente_id)
                    
                # Pausa entre ciclos
                await asyncio.sleep(self.config.pausa_entre_ciclos)
                
            except Exception as e:
                tentativas_erro += 1
                self.stats["total_erros"] += 1
                
                self.logger.error(f"Erro no ciclo do agente {agente_id} (tentativa {tentativas_erro}): {str(e)}")
                
                if tentativas_erro >= self.config.max_tentativas_erro:
                    self.logger.error(f"Agente {agente_id} excedeu máximo de tentativas. Reinicializando...")
                    
                    # Remover agente com problemas
                    if agente_id in self.agentes_ativos:
                        del self.agentes_ativos[agente_id]
                        
                    # Pausa antes de reinicializar
                    await asyncio.sleep(300)  # 5 minutos
                    tentativas_erro = 0
                else:
                    # Pausa progressiva baseada no número de erros
                    await asyncio.sleep(60 * tentativas_erro)
                    
    async def _executar_auto_descoberta(self, agente_id: str):
        """Executa auto-descoberta de novos sites"""
        try:
            # Lista de domínios para busca
            dominios_busca = [
                "huggingface.co",
                "replicate.com", 
                "runpod.io",
                "colab.research.google.com",
                "github.io",
                "vercel.app",
                "netlify.app"
            ]
            
            # Buscar subdomínios e páginas relacionadas
            for dominio in dominios_busca[:2]:  # Limitar para não sobrecarregar
                novos_sites = await self._descobrir_sites_relacionados(dominio)
                
                if novos_sites:
                    self.logger.info(f"Auto-descoberta encontrou {len(novos_sites)} novos sites via {dominio}")
                    
                    # Testar primeiro site descoberto
                    agente = self.agentes_ativos.get(agente_id)
                    if agente and novos_sites:
                        site_teste = novos_sites[0]
                        resultado = await agente.explorar_site_ia(site_teste)
                        
                        if resultado:
                            self.stats["total_sites_descobertos"] += 1
                            
        except Exception as e:
            self.logger.warning(f"Erro na auto-descoberta: {str(e)}")
            
    async def _descobrir_sites_relacionados(self, dominio: str) -> List[str]:
        """Descobre sites relacionados a um domínio"""
        try:
            # Configurar navegação anônima
            config_nav = ConfigNavegacao(usar_tor=False, selenium_headless=True)
            
            async with NavegacaoAnonima(config_nav) as nav:
                # Buscar na página principal
                response = await nav.requisicao_http_anonima(f"https://{dominio}")
                
                if response and response.status_code == 200:
                    html = response.text
                    
                    # Extrair links que podem ser de interesse
                    import re
                    
                    # Padrões para detectar links de IA/chat
                    padroes_ia = [
                        r'href="([^"]*(?:chat|ai|bot|assistant|gpt|llama|claude)[^"]*)"',
                        r'href="([^"]*(?:demo|playground|try)[^"]*)"',
                        r'href="(https?://[^"]*\.(?:ai|ml|chat)[^"]*)"'
                    ]
                    
                    sites_encontrados = []
                    
                    for padrao in padroes_ia:
                        matches = re.findall(padrao, html, re.IGNORECASE)
                        for match in matches:
                            if match.startswith('http') and len(match) > 10:
                                sites_encontrados.append(match)
                                
                    # Remover duplicatas e limitar
                    sites_unicos = list(set(sites_encontrados))[:5]
                    
                    return sites_unicos
                    
        except Exception as e:
            self.logger.debug(f"Erro ao descobrir sites relacionados a {dominio}: {str(e)}")
            
        return []
        
    async def sincronizar_memoria_coletiva(self):
        """Sincroniza todos os agentes com a memória coletiva"""
        try:
            self.logger.info("Iniciando sincronização com memória coletiva")
            
            for agente_id in self.agentes_ativos.keys():
                dados_sync = self.memoria_coletiva.sincronizar_agente(agente_id)
                self.logger.debug(f"Agente {agente_id} sincronizado")
                
            self.stats["ultima_sincronizacao"] = datetime.now().isoformat()
            
            # Log estatísticas da memória
            estado = self.memoria_coletiva.obter_estado_memoria()
            self.logger.info(f"Memória coletiva: {estado.total_sites_mapeados} sites, {estado.total_agentes_ativos} agentes ativos")
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização: {str(e)}")
            
    async def gerar_reports_periodicos(self):
        """Gera reports periódicos de todos os agentes"""
        try:
            self.logger.info("Gerando reports periódicos")
            
            # Report coletivo
            report_coletivo = await self.sistema_reports.gerar_report_coletivo()
            
            # Reports individuais
            agentes_ids = list(self.agentes_ativos.keys())
            for agente_id in agentes_ids:
                await self.sistema_reports.gerar_report_individual(agente_id)
                
            self.stats["ultimo_report"] = datetime.now().isoformat()
            
            # Log resumo
            self.logger.info(f"Reports gerados - {len(agentes_ids)} individuais + 1 coletivo")
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar reports: {str(e)}")
            
    async def executar_manutencao_periodica(self):
        """Executa tarefas de manutenção periódica"""
        try:
            # Limpeza de logs antigos (manter últimos 30 dias)
            await self._limpar_logs_antigos()
            
            # Compactação de dados históricos
            await self._compactar_dados_historicos()
            
            # Verificação de saúde dos agentes
            await self._verificar_saude_agentes()
            
            self.logger.info("Manutenção periódica concluída")
            
        except Exception as e:
            self.logger.error(f"Erro na manutenção: {str(e)}")
            
    async def _limpar_logs_antigos(self, dias_manter: int = 30):
        """Remove logs antigos"""
        try:
            logs_path = Path("../logs")
            cutoff_date = datetime.now() - timedelta(days=dias_manter)
            
            arquivos_removidos = 0
            
            for arquivo in logs_path.rglob("*.log"):
                if arquivo.stat().st_mtime < cutoff_date.timestamp():
                    arquivo.unlink()
                    arquivos_removidos += 1
                    
            if arquivos_removidos > 0:
                self.logger.info(f"Removidos {arquivos_removidos} arquivos de log antigos")
                
        except Exception as e:
            self.logger.warning(f"Erro ao limpar logs: {str(e)}")
            
    async def _compactar_dados_historicos(self):
        """Compacta dados históricos antigos"""
        try:
            # Implementar compactação de histórico de conversas
            historico_path = Path("../data/historico_conversas")
            
            if historico_path.exists():
                # Contar arquivos
                arquivos = list(historico_path.glob("*.json"))
                
                if len(arquivos) > 1000:  # Se há muitos arquivos
                    self.logger.info(f"Iniciando compactação de {len(arquivos)} arquivos históricos")
                    # Aqui seria implementada a lógica de compactação
                    
        except Exception as e:
            self.logger.warning(f"Erro na compactação: {str(e)}")
            
    async def _verificar_saude_agentes(self):
        """Verifica saúde dos agentes ativos"""
        try:
            agentes_com_problema = []
            
            for agente_id, agente in self.agentes_ativos.items():
                # Verificar se agente está respondendo
                try:
                    report = await agente.gerar_report_individual()
                    if not report:
                        agentes_com_problema.append(agente_id)
                except Exception:
                    agentes_com_problema.append(agente_id)
                    
            if agentes_com_problema:
                self.logger.warning(f"Agentes com problemas detectados: {agentes_com_problema}")
                
        except Exception as e:
            self.logger.warning(f"Erro na verificação de saúde: {str(e)}")
            
    async def executar_operacao_24x7(self):
        """Executa operação 24/7 dos agentes exploradores"""
        try:
            self.logger.info("Iniciando operação 24/7 dos agentes exploradores")
            
            # Inicializar agentes
            agentes_ids = [f"explorer_{i:03d}" for i in range(1, self.config.max_agentes_simultaneos + 1)]
            
            # Criar tasks para cada agente
            agent_tasks = []
            for agente_id in agentes_ids:
                task = asyncio.create_task(self.executar_ciclo_agente(agente_id))
                self.tasks_agentes[agente_id] = task
                agent_tasks.append(task)
                
            # Task de sincronização periódica
            sync_task = asyncio.create_task(self._loop_sincronizacao())
            
            # Task de reports periódicos
            reports_task = asyncio.create_task(self._loop_reports())
            
            # Task de manutenção
            manutencao_task = asyncio.create_task(self._loop_manutencao())
            
            # Aguardar shutdown ou erro crítico
            all_tasks = agent_tasks + [sync_task, reports_task, manutencao_task]
            
            try:
                await asyncio.gather(*all_tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"Erro crítico na operação: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Erro fatal na operação 24/7: {str(e)}")
            raise
        finally:
            await self._shutdown_graceful()
            
    async def _loop_sincronizacao(self):
        """Loop de sincronização periódica"""
        while not self.shutdown_event.is_set():
            try:
                await self.sincronizar_memoria_coletiva()
                await asyncio.sleep(self.config.intervalo_sincronizacao)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de sincronização: {str(e)}")
                await asyncio.sleep(60)
                
    async def _loop_reports(self):
        """Loop de geração de reports"""
        while not self.shutdown_event.is_set():
            try:
                await self.gerar_reports_periodicos()
                await asyncio.sleep(self.config.intervalo_reports)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de reports: {str(e)}")
                await asyncio.sleep(300)
                
    async def _loop_manutencao(self):
        """Loop de manutenção periódica"""
        while not self.shutdown_event.is_set():
            try:
                await self.executar_manutencao_periodica()
                await asyncio.sleep(86400)  # 24 horas
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de manutenção: {str(e)}")
                await asyncio.sleep(3600)
                
    async def _shutdown_graceful(self):
        """Executa shutdown graceful de todos os componentes"""
        try:
            self.logger.info("Iniciando shutdown graceful...")
            
            # Cancelar todas as tasks
            for agente_id, task in self.tasks_agentes.items():
                if not task.done():
                    task.cancel()
                    self.logger.info(f"Task do agente {agente_id} cancelada")
                    
            # Aguardar finalização das tasks
            if self.tasks_agentes:
                await asyncio.gather(*self.tasks_agentes.values(), return_exceptions=True)
                
            # Finalizar agentes
            for agente_id, agente in self.agentes_ativos.items():
                try:
                    # Salvar estado final
                    await agente.gerar_report_individual()
                    self.logger.info(f"Agente {agente_id} finalizado")
                except Exception as e:
                    self.logger.warning(f"Erro ao finalizar agente {agente_id}: {str(e)}")
                    
            # Salvar estatísticas finais
            await self._salvar_stats_finais()
            
            self.logger.info("Shutdown graceful concluído")
            
        except Exception as e:
            self.logger.error(f"Erro no shutdown graceful: {str(e)}")
            
    async def _salvar_stats_finais(self):
        """Salva estatísticas finais da operação"""
        try:
            self.stats["fim_operacao"] = datetime.now().isoformat()
            
            stats_path = Path("../data/reports/stats_operacao_final.json")
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
                
            self.logger.info("Estatísticas finais salvas")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar estatísticas: {str(e)}")
            
    def obter_status_operacao(self) -> Dict:
        """Obtém status atual da operação"""
        return {
            "agentes_ativos": len(self.agentes_ativos),
            "tasks_ativas": len([t for t in self.tasks_agentes.values() if not t.done()]),
            "estatisticas": self.stats.copy(),
            "memoria_coletiva": asdict(self.memoria_coletiva.obter_estado_memoria()),
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """Função principal para execução standalone"""
    try:
        # Configuração para operação 24/7
        config = ConfigCoordenador(
            max_agentes_simultaneos=3,  # Começar com 3 agentes
            intervalo_sincronizacao=300,  # 5 minutos
            intervalo_reports=3600,  # 1 hora
            modo_24x7=True,
            auto_descoberta_ativa=True
        )
        
        coordenador = CoordenadorExploradores(config)
        
        # Log de inicialização
        coordenador.logger.info("=== EXÉRCITO DE AGENTES EXPLORADORES DE IA ===")
        coordenador.logger.info("Iniciando operação de exploração autônoma 24/7")
        coordenador.logger.info(f"Configuração: {config.max_agentes_simultaneos} agentes, sync={config.intervalo_sincronizacao}s")
        
        # Executar operação
        await coordenador.executar_operacao_24x7()
        
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário")
    except Exception as e:
        print(f"Erro fatal: {str(e)}")
        logging.error(f"Erro fatal na main: {str(e)}")
    finally:
        print("Sistema finalizado")


if __name__ == "__main__":
    # Executar sistema
    asyncio.run(main())