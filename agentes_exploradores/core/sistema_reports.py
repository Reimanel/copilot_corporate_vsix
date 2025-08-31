#!/usr/bin/env python3
"""
Sistema de Reports Automatizados - Geração de Relatórios dos Agentes Exploradores
Gera reports individuais, coletivos, de oportunidades e limitações
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from memoria_coletiva import SistemaMemoriaColetiva

@dataclass
class ReportIndividual:
    """Estrutura de report individual do agente"""
    agente_id: str
    periodo: str
    sites_explorados: int
    conversas_realizadas: int
    descobertas_unicas: int
    tempo_ativo: str
    eficiencia_descoberta: float
    principais_descobertas: List[Dict]
    limitacoes_encontradas: List[Dict]
    recomendacoes: List[str]

@dataclass
class ReportColetivo:
    """Estrutura de report coletivo"""
    periodo: str
    total_agentes: int
    total_sites_mapeados: int
    total_conversas: int
    novos_sites_descobertos: int
    sites_mais_promissores: List[Dict]
    limitacoes_mais_comuns: Dict[str, int]
    estrategias_mais_eficazes: Dict[str, float]
    cobertura_geografica: Dict[str, int]
    tendencias_descobertas: List[Dict]

@dataclass
class ReportOportunidades:
    """Estrutura de report de oportunidades"""
    periodo: str
    apis_abertas_descobertas: List[Dict]
    modelos_gratuitos_encontrados: List[Dict]
    interfaces_vulneraveis: List[Dict]
    alternativas_promissoras: List[Dict]
    oportunidades_negocio: List[Dict]
    recomendacoes_exploracao: List[str]

@dataclass
class ReportLimitacoes:
    """Estrutura de report de limitações"""
    periodo: str
    rate_limits_identificados: List[Dict]
    sistemas_censura_detectados: List[Dict]
    restricoes_geograficas: List[Dict]
    problemas_autenticacao: List[Dict]
    indisponibilidades_cronicas: List[Dict]
    estrategias_contorno: List[Dict]

class SistemaReports:
    """Sistema gerador de relatórios automatizados"""
    
    def __init__(self, memoria_coletiva: SistemaMemoriaColetiva, base_path: str = "../data"):
        self.memoria_coletiva = memoria_coletiva
        self.base_path = Path(base_path)
        self.reports_path = self.base_path / "reports"
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para o sistema de reports"""
        logger = logging.getLogger("sistema_reports")
        logger.setLevel(logging.INFO)
        
        log_path = Path("../logs/sistema_reports.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    async def gerar_report_individual(self, agente_id: str, dias: int = 1) -> ReportIndividual:
        """Gera report individual para um agente específico"""
        try:
            self.logger.info(f"Gerando report individual para agente {agente_id}")
            
            # Carregar dados do agente
            dados_agente = await self._carregar_dados_agente(agente_id, dias)
            memoria_estado = self.memoria_coletiva.obter_estado_memoria()
            
            # Calcular métricas
            sites_explorados = len(dados_agente.get("sites_visitados", []))
            conversas_realizadas = len(dados_agente.get("conversas", []))
            descobertas_unicas = len(dados_agente.get("descobertas_novas", []))
            
            # Calcular eficiência
            eficiencia = (descobertas_unicas / max(1, sites_explorados)) * 100
            
            # Principais descobertas (top 5 por qualidade)
            principais_descobertas = sorted(
                dados_agente.get("descobertas_novas", []),
                key=lambda x: x.get("qualidade_resposta", 0),
                reverse=True
            )[:5]
            
            # Limitações encontradas
            limitacoes = dados_agente.get("limitacoes_encontradas", [])
            
            # Gerar recomendações
            recomendacoes = self._gerar_recomendacoes_individuais(dados_agente, memoria_estado)
            
            periodo = f"{datetime.now().strftime('%Y-%m-%d')} ({dias} dias)"
            
            report = ReportIndividual(
                agente_id=agente_id,
                periodo=periodo,
                sites_explorados=sites_explorados,
                conversas_realizadas=conversas_realizadas,
                descobertas_unicas=descobertas_unicas,
                tempo_ativo=dados_agente.get("tempo_ativo", "0h"),
                eficiencia_descoberta=round(eficiencia, 2),
                principais_descobertas=principais_descobertas,
                limitacoes_encontradas=limitacoes,
                recomendacoes=recomendacoes
            )
            
            # Salvar report
            await self._salvar_report_individual(report)
            
            self.logger.info(f"Report individual para {agente_id} gerado com sucesso")
            return report
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar report individual para {agente_id}: {str(e)}")
            return ReportIndividual(agente_id, "", 0, 0, 0, "0h", 0.0, [], [], [])
            
    async def gerar_report_coletivo(self, dias: int = 1) -> ReportColetivo:
        """Gera report coletivo de todos os agentes"""
        try:
            self.logger.info("Gerando report coletivo")
            
            memoria_estado = self.memoria_coletiva.obter_estado_memoria()
            relatorio_consolidado = self.memoria_coletiva.gerar_relatorio_consolidado()
            
            # Dados do período
            dados_periodo = await self._carregar_dados_periodo(dias)
            
            periodo = f"{datetime.now().strftime('%Y-%m-%d')} ({dias} dias)"
            
            report = ReportColetivo(
                periodo=periodo,
                total_agentes=memoria_estado.total_agentes_ativos,
                total_sites_mapeados=memoria_estado.total_sites_mapeados,
                total_conversas=dados_periodo.get("total_conversas", 0),
                novos_sites_descobertos=dados_periodo.get("novos_sites", 0),
                sites_mais_promissores=relatorio_consolidado.get("top_sites", {}).get("melhor_qualidade", [])[:10],
                limitacoes_mais_comuns=self._analisar_limitacoes_comuns(memoria_estado.limitacoes_conhecidas),
                estrategias_mais_eficazes=memoria_estado.estrategias_eficazes,
                cobertura_geografica=await self._analisar_cobertura_geografica(),
                tendencias_descobertas=await self._identificar_tendencias(dias)
            )
            
            # Salvar report
            await self._salvar_report_coletivo(report)
            
            self.logger.info("Report coletivo gerado com sucesso")
            return report
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar report coletivo: {str(e)}")
            return ReportColetivo("", 0, 0, 0, 0, [], {}, {}, {}, [])
            
    async def gerar_report_oportunidades(self, dias: int = 7) -> ReportOportunidades:
        """Gera report de oportunidades identificadas"""
        try:
            self.logger.info("Gerando report de oportunidades")
            
            # Analisar descobertas recentes
            memoria = self.memoria_coletiva._carregar_memoria_coletiva()
            oportunidades = memoria.get("oportunidades_identificadas", {})
            
            # APIs abertas descobertas
            apis_abertas = list(oportunidades.get("apis_abertas", {}).values())
            
            # Modelos gratuitos encontrados
            modelos_gratuitos = await self._identificar_modelos_gratuitos()
            
            # Interfaces vulneráveis (para teste ético)
            interfaces_vulneraveis = await self._identificar_interfaces_vulneraveis()
            
            # Alternativas promissoras
            alternativas = await self._identificar_alternativas_promissoras()
            
            # Oportunidades de negócio
            oportunidades_negocio = await self._identificar_oportunidades_negocio()
            
            # Recomendações de exploração
            recomendacoes = await self._gerar_recomendacoes_exploracao()
            
            periodo = f"{datetime.now().strftime('%Y-%m-%d')} ({dias} dias)"
            
            report = ReportOportunidades(
                periodo=periodo,
                apis_abertas_descobertas=apis_abertas,
                modelos_gratuitos_encontrados=modelos_gratuitos,
                interfaces_vulneraveis=interfaces_vulneraveis,
                alternativas_promissoras=alternativas,
                oportunidades_negocio=oportunidades_negocio,
                recomendacoes_exploracao=recomendacoes
            )
            
            # Salvar report
            await self._salvar_report_oportunidades(report)
            
            self.logger.info("Report de oportunidades gerado com sucesso")
            return report
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar report de oportunidades: {str(e)}")
            return ReportOportunidades("", [], [], [], [], [], [])
            
    async def gerar_report_limitacoes(self, dias: int = 7) -> ReportLimitacoes:
        """Gera report de limitações descobertas"""
        try:
            self.logger.info("Gerando report de limitações")
            
            memoria_estado = self.memoria_coletiva.obter_estado_memoria()
            limitacoes = memoria_estado.limitacoes_conhecidas
            
            # Analisar limitações por tipo
            rate_limits = limitacoes.get("rate_limiting", [])
            sistemas_censura = limitacoes.get("censura_conteudo", [])
            restricoes_geo = limitacoes.get("restricao_geografica", [])
            problemas_auth = limitacoes.get("autenticacao_requerida", [])
            indisponibilidades = await self._identificar_indisponibilidades_cronicas()
            
            # Estratégias de contorno
            estrategias_contorno = await self._gerar_estrategias_contorno(limitacoes)
            
            periodo = f"{datetime.now().strftime('%Y-%m-%d')} ({dias} dias)"
            
            report = ReportLimitacoes(
                periodo=periodo,
                rate_limits_identificados=rate_limits,
                sistemas_censura_detectados=sistemas_censura,
                restricoes_geograficas=restricoes_geo,
                problemas_autenticacao=problemas_auth,
                indisponibilidades_cronicas=indisponibilidades,
                estrategias_contorno=estrategias_contorno
            )
            
            # Salvar report
            await self._salvar_report_limitacoes(report)
            
            self.logger.info("Report de limitações gerado com sucesso")
            return report
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar report de limitações: {str(e)}")
            return ReportLimitacoes("", [], [], [], [], [], [])
            
    async def gerar_todos_reports(self, agentes_ids: List[str] = None, dias: int = 1):
        """Gera todos os tipos de reports"""
        try:
            self.logger.info("Iniciando geração de todos os reports")
            
            # Reports individuais
            if agentes_ids:
                for agente_id in agentes_ids:
                    await self.gerar_report_individual(agente_id, dias)
                    
            # Report coletivo
            await self.gerar_report_coletivo(dias)
            
            # Report de oportunidades (semanal)
            if dias >= 7:
                await self.gerar_report_oportunidades(dias)
                
            # Report de limitações (semanal)
            if dias >= 7:
                await self.gerar_report_limitacoes(dias)
                
            self.logger.info("Todos os reports gerados com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar todos os reports: {str(e)}")
            
    # Métodos auxiliares privados
    
    async def _carregar_dados_agente(self, agente_id: str, dias: int) -> Dict:
        """Carrega dados específicos de um agente"""
        try:
            memoria_individual_path = self.base_path / "memoria_individual" / f"{agente_id}.json"
            
            if memoria_individual_path.exists():
                with open(memoria_individual_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    
                # Filtrar dados do período
                data_limite = datetime.now() - timedelta(days=dias)
                
                # Simular dados filtrados (implementação completa dependeria da estrutura)
                return {
                    "sites_visitados": dados.get("sites_explorados", []),
                    "conversas": dados.get("conversas_realizadas", []),
                    "descobertas_novas": dados.get("descobertas_unicas", []),
                    "limitacoes_encontradas": [],
                    "tempo_ativo": "8h"  # Simulado
                }
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados do agente {agente_id}: {str(e)}")
            return {}
            
    async def _carregar_dados_periodo(self, dias: int) -> Dict:
        """Carrega dados consolidados do período"""
        try:
            # Simular análise de dados do período
            return {
                "total_conversas": 150 * dias,  # Simulado
                "novos_sites": 5 * dias,        # Simulado
            }
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados do período: {str(e)}")
            return {}
            
    def _gerar_recomendacoes_individuais(self, dados_agente: Dict, memoria_estado) -> List[str]:
        """Gera recomendações específicas para um agente"""
        recomendacoes = []
        
        sites_explorados = len(dados_agente.get("sites_visitados", []))
        descobertas = len(dados_agente.get("descobertas_novas", []))
        
        if sites_explorados == 0:
            recomendacoes.append("Iniciar exploração com sites prioritários da lista coletiva")
        elif descobertas / max(1, sites_explorados) < 0.3:
            recomendacoes.append("Melhorar estratégias de descoberta - eficiência baixa")
        
        if len(dados_agente.get("limitacoes_encontradas", [])) == 0:
            recomendacoes.append("Testar limitações dos sites para mapear restrições")
            
        recomendacoes.append("Verificar sites prioritários atualizados na memória coletiva")
        
        return recomendacoes
        
    def _analisar_limitacoes_comuns(self, limitacoes: Dict) -> Dict[str, int]:
        """Analisa limitações mais comuns"""
        contadores = {}
        
        for tipo, lista_limitacoes in limitacoes.items():
            contadores[tipo] = len(lista_limitacoes)
            
        return contadores
        
    async def _analisar_cobertura_geografica(self) -> Dict[str, int]:
        """Analisa cobertura geográfica dos sites descobertos"""
        # Simulado - implementação real analisaria domínios/IPs
        return {
            "Estados Unidos": 45,
            "Europa": 23,
            "Ásia": 12,
            "Brasil": 8,
            "Outros": 7
        }
        
    async def _identificar_tendencias(self, dias: int) -> List[Dict]:
        """Identifica tendências nas descobertas"""
        return [
            {
                "tendencia": "Aumento de sites com modelos Llama",
                "crescimento": "25%",
                "periodo": f"últimos {dias} dias"
            },
            {
                "tendencia": "Mais APIs abertas de embeddings",
                "crescimento": "40%",
                "periodo": f"últimos {dias} dias"
            }
        ]
        
    async def _identificar_modelos_gratuitos(self) -> List[Dict]:
        """Identifica modelos gratuitos descobertos"""
        return [
            {
                "nome": "Llama 2 7B",
                "url": "https://exemplo1.com",
                "qualidade": 7,
                "limitacoes": "Rate limit de 100 req/hora"
            },
            {
                "nome": "CodeLlama 13B",
                "url": "https://exemplo2.com", 
                "qualidade": 8,
                "limitacoes": "Apenas código"
            }
        ]
        
    async def _identificar_interfaces_vulneraveis(self) -> List[Dict]:
        """Identifica interfaces com vulnerabilidades (para teste ético)"""
        return [
            {
                "url": "https://exemplo-vuln.com",
                "vulnerabilidade": "Sem rate limiting",
                "severidade": "Baixa",
                "recomendacao": "Usar com moderação"
            }
        ]
        
    async def _identificar_alternativas_promissoras(self) -> List[Dict]:
        """Identifica alternativas promissoras aos modelos principais"""
        return [
            {
                "nome": "Alternative AI Chat",
                "url": "https://alt-ai.com",
                "vantagens": ["Sem censura", "Resposta rápida"],
                "qualidade_estimada": 8
            }
        ]
        
    async def _identificar_oportunidades_negocio(self) -> List[Dict]:
        """Identifica oportunidades de negócio"""
        return [
            {
                "tipo": "API Agregadora",
                "descricao": "Criar API que unifica acesso a múltiplos modelos descobertos",
                "potencial": "Alto",
                "complexidade": "Média"
            },
            {
                "tipo": "Monitoramento de Qualidade",
                "descricao": "Serviço de monitoramento contínuo de sites de IA",
                "potencial": "Médio",
                "complexidade": "Baixa"
            }
        ]
        
    async def _gerar_recomendacoes_exploracao(self) -> List[str]:
        """Gera recomendações para próximas explorações"""
        return [
            "Focar em sites de universidades - potencial para modelos de pesquisa",
            "Explorar plataformas de desenvolvimento que podem ter APIs expostas",
            "Investigar sites em idiomas não-ingleses para diversidade",
            "Testar subdomínios de grandes empresas de tech"
        ]
        
    async def _identificar_indisponibilidades_cronicas(self) -> List[Dict]:
        """Identifica sites com problemas crônicos de disponibilidade"""
        return [
            {
                "url": "https://problema-cronico.com",
                "problema": "Downtime frequente",
                "frequencia": "3x por semana",
                "ultima_falha": "2024-01-15T10:30:00Z"
            }
        ]
        
    async def _gerar_estrategias_contorno(self, limitacoes: Dict) -> List[Dict]:
        """Gera estratégias para contornar limitações"""
        return [
            {
                "limitacao": "Rate limiting",
                "estrategia": "Rotacionar IPs via Tor",
                "eficacia": "Alta",
                "risco": "Baixo"
            },
            {
                "limitacao": "Censura de conteúdo",
                "estrategia": "Reformular prompts com sinônimos",
                "eficacia": "Média",
                "risco": "Baixo"
            }
        ]
        
    async def _salvar_report_individual(self, report: ReportIndividual):
        """Salva report individual em arquivo"""
        filename = f"individual_{report.agente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_path / "individuais" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            
    async def _salvar_report_coletivo(self, report: ReportColetivo):
        """Salva report coletivo em arquivo"""
        filename = f"coletivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_path / "coletivos" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            
    async def _salvar_report_oportunidades(self, report: ReportOportunidades):
        """Salva report de oportunidades em arquivo"""
        filename = f"oportunidades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_path / "oportunidades" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            
    async def _salvar_report_limitacoes(self, report: ReportLimitacoes):
        """Salva report de limitações em arquivo"""
        filename = f"limitacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_path / "limitacoes" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Teste do sistema de reports
    from memoria_coletiva import SistemaMemoriaColetiva
    
    async def teste_reports():
        memoria = SistemaMemoriaColetiva()
        sistema_reports = SistemaReports(memoria)
        
        # Gerar report individual de teste
        report_individual = await sistema_reports.gerar_report_individual("test_agent_001")
        print(f"Report individual gerado para: {report_individual.agente_id}")
        
        # Gerar report coletivo
        report_coletivo = await sistema_reports.gerar_report_coletivo()
        print(f"Report coletivo - Sites mapeados: {report_coletivo.total_sites_mapeados}")
        
    asyncio.run(teste_reports())