#!/usr/bin/env python3
"""
Sistema de Memória Coletiva - Coordenação de Agentes Exploradores
Gerencia conhecimento compartilhado entre todos os agentes exploradores
"""

import json
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

@dataclass
class EstadoMemoriaColetiva:
    """Estado atual da memória coletiva"""
    total_sites_mapeados: int
    total_agentes_ativos: int
    ultima_atualizacao: str
    sites_prioritarios: List[str]
    estrategias_eficazes: Dict[str, float]
    limitacoes_conhecidas: Dict[str, List[str]]

class SistemaMemoriaColetiva:
    """Gerenciador da memória coletiva compartilhada"""
    
    def __init__(self, base_path: str = "../data"):
        self.base_path = Path(base_path)
        self.memoria_coletiva_path = self.base_path / "memoria_coletiva.json"
        self.lock = threading.Lock()
        self.logger = self._setup_logging()
        
        # Inicializar estrutura de memória
        self._inicializar_memoria_coletiva()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para o sistema de memória"""
        logger = logging.getLogger("memoria_coletiva")
        logger.setLevel(logging.INFO)
        
        log_path = Path("../logs/memoria_coletiva.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def _inicializar_memoria_coletiva(self):
        """Inicializa a estrutura de memória coletiva"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        if not self.memoria_coletiva_path.exists():
            memoria_inicial = {
                "metadata": {
                    "versao": "1.0",
                    "criado_em": datetime.now().isoformat(),
                    "ultima_atualizacao": datetime.now().isoformat(),
                    "total_atualizacoes": 0
                },
                "sites_mapeados": {},
                "limitacoes_descobertas": {
                    "rate_limiting": [],
                    "censura_conteudo": [],
                    "restricao_geografica": [],
                    "autenticacao_requerida": []
                },
                "oportunidades_identificadas": {
                    "apis_abertas": {},
                    "modelos_gratuitos": {},
                    "interfaces_instáveis": {},
                    "alternativas_descobertas": {}
                },
                "estrategias_eficazes": {
                    "conversacao_natural": 0.0,
                    "teste_limitacoes": 0.0,
                    "extracao_metadata": 0.0,
                    "navegacao_anonima": 0.0
                },
                "agentes_status": {},
                "descobertas_recentes": [],
                "sites_prioritarios": [
                    "https://chat.openai.com",
                    "https://claude.ai",
                    "https://bard.google.com",
                    "https://poe.com",
                    "https://character.ai"
                ]
            }
            
            self._salvar_memoria_coletiva(memoria_inicial)
            self.logger.info("Memória coletiva inicializada")
            
    def _carregar_memoria_coletiva(self) -> Dict:
        """Carrega memória coletiva do arquivo"""
        try:
            with open(self.memoria_coletiva_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar memória coletiva: {str(e)}")
            return {}
            
    def _salvar_memoria_coletiva(self, memoria: Dict):
        """Salva memória coletiva no arquivo"""
        try:
            with self.lock:
                memoria["metadata"]["ultima_atualizacao"] = datetime.now().isoformat()
                memoria["metadata"]["total_atualizacoes"] = memoria["metadata"].get("total_atualizacoes", 0) + 1
                
                with open(self.memoria_coletiva_path, 'w', encoding='utf-8') as f:
                    json.dump(memoria, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"Erro ao salvar memória coletiva: {str(e)}")
            
    def registrar_descoberta_site(self, agente_id: str, site_ia: Dict) -> bool:
        """Registra nova descoberta de site na memória coletiva"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            url = site_ia["url"]
            
            # Verificar se site já existe
            if url in memoria["sites_mapeados"]:
                # Atualizar informações existentes
                site_existente = memoria["sites_mapeados"][url]
                site_existente["ultima_verificacao"] = datetime.now().isoformat()
                site_existente["verificacoes_totais"] = site_existente.get("verificacoes_totais", 0) + 1
                site_existente["agentes_verificadores"].append(agente_id)
                
                # Atualizar scores com média ponderada
                peso_novo = 0.3
                for metric in ["qualidade_resposta", "nivel_censura", "velocidade_resposta", "facilidade_acesso"]:
                    if metric in site_ia and metric in site_existente:
                        valor_atual = site_existente[metric]
                        valor_novo = site_ia[metric]
                        site_existente[metric] = valor_atual * (1 - peso_novo) + valor_novo * peso_novo
                        
                self.logger.info(f"Site {url} atualizado por agente {agente_id}")
            else:
                # Adicionar novo site
                site_ia["descoberto_por"] = agente_id
                site_ia["primeira_descoberta"] = datetime.now().isoformat()
                site_ia["ultima_verificacao"] = datetime.now().isoformat()
                site_ia["verificacoes_totais"] = 1
                site_ia["agentes_verificadores"] = [agente_id]
                
                memoria["sites_mapeados"][url] = site_ia
                
                # Adicionar às descobertas recentes
                memoria["descobertas_recentes"].append({
                    "url": url,
                    "agente_id": agente_id,
                    "timestamp": datetime.now().isoformat(),
                    "tipo": "novo_site"
                })
                
                self.logger.info(f"Novo site {url} descoberto por agente {agente_id}")
                
            # Atualizar status do agente
            memoria["agentes_status"][agente_id] = {
                "ultima_atividade": datetime.now().isoformat(),
                "sites_descobertos": len([s for s in memoria["sites_mapeados"].values() 
                                        if s.get("descoberto_por") == agente_id]),
                "total_verificacoes": len([s for s in memoria["sites_mapeados"].values() 
                                        if agente_id in s.get("agentes_verificadores", [])]),
                "status": "ativo"
            }
            
            self._salvar_memoria_coletiva(memoria)
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar descoberta: {str(e)}")
            return False
            
    def registrar_limitacao(self, agente_id: str, url: str, tipo_limitacao: str, detalhes: str):
        """Registra limitação descoberta por um agente"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            limitacao = {
                "url": url,
                "agente_id": agente_id,
                "detalhes": detalhes,
                "timestamp": datetime.now().isoformat()
            }
            
            if tipo_limitacao in memoria["limitacoes_descobertas"]:
                memoria["limitacoes_descobertas"][tipo_limitacao].append(limitacao)
            else:
                memoria["limitacoes_descobertas"][tipo_limitacao] = [limitacao]
                
            self.logger.info(f"Limitação '{tipo_limitacao}' registrada para {url} por {agente_id}")
            self._salvar_memoria_coletiva(memoria)
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar limitação: {str(e)}")
            
    def atualizar_estrategia_eficacia(self, estrategia: str, sucesso: bool, fator_peso: float = 1.0):
        """Atualiza eficácia de uma estratégia específica"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            if estrategia not in memoria["estrategias_eficazes"]:
                memoria["estrategias_eficazes"][estrategia] = 0.5
                
            score_atual = memoria["estrategias_eficazes"][estrategia]
            ajuste = 0.1 * fator_peso if sucesso else -0.05 * fator_peso
            novo_score = max(0.0, min(1.0, score_atual + ajuste))
            
            memoria["estrategias_eficazes"][estrategia] = novo_score
            
            self.logger.debug(f"Estratégia '{estrategia}' atualizada: {score_atual:.3f} -> {novo_score:.3f}")
            self._salvar_memoria_coletiva(memoria)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar estratégia: {str(e)}")
            
    def obter_sites_prioritarios(self, agente_id: str, limite: int = 10) -> List[str]:
        """Obtém lista de sites prioritários para exploração"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            # Sites da lista prioritária que ainda não foram totalmente explorados
            sites_prioritarios = []
            
            for url in memoria["sites_prioritarios"]:
                site_info = memoria["sites_mapeados"].get(url, {})
                
                # Critérios para priorização:
                # 1. Nunca foi explorado
                # 2. Última verificação foi há mais de 24h
                # 3. Poucos agentes verificaram
                
                if not site_info:
                    sites_prioritarios.append(url)
                else:
                    ultima_verificacao = datetime.fromisoformat(
                        site_info.get("ultima_verificacao", "2020-01-01T00:00:00")
                    )
                    tempo_desde_ultima = datetime.now() - ultima_verificacao
                    
                    if (tempo_desde_ultima > timedelta(hours=24) or 
                        len(site_info.get("agentes_verificadores", [])) < 3):
                        sites_prioritarios.append(url)
                        
            # Adicionar sites com baixa qualidade para re-verificação
            for url, site_info in memoria["sites_mapeados"].items():
                if (site_info.get("qualidade_resposta", 0) < 5 and 
                    url not in sites_prioritarios):
                    sites_prioritarios.append(url)
                    
            return sites_prioritarios[:limite]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter sites prioritários: {str(e)}")
            return []
            
    def obter_estado_memoria(self) -> EstadoMemoriaColetiva:
        """Obtém estado atual da memória coletiva"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            return EstadoMemoriaColetiva(
                total_sites_mapeados=len(memoria["sites_mapeados"]),
                total_agentes_ativos=len([a for a in memoria["agentes_status"].values() 
                                        if a.get("status") == "ativo"]),
                ultima_atualizacao=memoria["metadata"]["ultima_atualizacao"],
                sites_prioritarios=memoria["sites_prioritarios"],
                estrategias_eficazes=memoria["estrategias_eficazes"],
                limitacoes_conhecidas=memoria["limitacoes_descobertas"]
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estado da memória: {str(e)}")
            return EstadoMemoriaColetiva(0, 0, "", [], {}, {})
            
    def obter_melhores_sites(self, criterio: str = "qualidade", limite: int = 10) -> List[Dict]:
        """Obtém melhores sites baseado em critério específico"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            sites = list(memoria["sites_mapeados"].values())
            
            # Ordenar baseado no critério
            if criterio == "qualidade":
                sites.sort(key=lambda x: x.get("qualidade_resposta", 0), reverse=True)
            elif criterio == "velocidade":
                sites.sort(key=lambda x: x.get("velocidade_resposta", 0), reverse=True)
            elif criterio == "acesso":
                sites.sort(key=lambda x: x.get("facilidade_acesso", 0), reverse=True)
            elif criterio == "disponibilidade":
                sites.sort(key=lambda x: x.get("disponibilidade", 0), reverse=True)
                
            return sites[:limite]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter melhores sites: {str(e)}")
            return []
            
    def sincronizar_agente(self, agente_id: str) -> Dict:
        """Sincroniza um agente com a memória coletiva"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            # Marcar agente como ativo
            memoria["agentes_status"][agente_id] = memoria["agentes_status"].get(agente_id, {})
            memoria["agentes_status"][agente_id]["ultima_sincronizacao"] = datetime.now().isoformat()
            memoria["agentes_status"][agente_id]["status"] = "ativo"
            
            self._salvar_memoria_coletiva(memoria)
            
            # Retornar informações relevantes para o agente
            return {
                "sites_prioritarios": self.obter_sites_prioritarios(agente_id),
                "estrategias_eficazes": memoria["estrategias_eficazes"],
                "limitacoes_recentes": self._obter_limitacoes_recentes(),
                "descobertas_recentes": memoria["descobertas_recentes"][-10:],
                "estado_geral": asdict(self.obter_estado_memoria())
            }
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização do agente {agente_id}: {str(e)}")
            return {}
            
    def _obter_limitacoes_recentes(self, horas: int = 24) -> Dict:
        """Obtém limitações descobertas nas últimas N horas"""
        try:
            memoria = self._carregar_memoria_coletiva()
            limitacoes_recentes = {}
            
            tempo_limite = datetime.now() - timedelta(hours=horas)
            
            for tipo, limitacoes in memoria["limitacoes_descobertas"].items():
                recentes = []
                for limitacao in limitacoes:
                    timestamp = datetime.fromisoformat(limitacao["timestamp"])
                    if timestamp > tempo_limite:
                        recentes.append(limitacao)
                        
                if recentes:
                    limitacoes_recentes[tipo] = recentes
                    
            return limitacoes_recentes
            
        except Exception as e:
            self.logger.error(f"Erro ao obter limitações recentes: {str(e)}")
            return {}
            
    def gerar_relatorio_consolidado(self) -> Dict:
        """Gera relatório consolidado da memória coletiva"""
        try:
            memoria = self._carregar_memoria_coletiva()
            estado = self.obter_estado_memoria()
            
            relatorio = {
                "timestamp": datetime.now().isoformat(),
                "resumo_geral": {
                    "total_sites_mapeados": estado.total_sites_mapeados,
                    "total_agentes_ativos": estado.total_agentes_ativos,
                    "ultima_atualizacao": estado.ultima_atualizacao
                },
                "top_sites": {
                    "melhor_qualidade": self.obter_melhores_sites("qualidade", 5),
                    "mais_rapidos": self.obter_melhores_sites("velocidade", 5),
                    "mais_acessiveis": self.obter_melhores_sites("acesso", 5)
                },
                "estrategias_eficazes": estado.estrategias_eficazes,
                "limitacoes_descobertas": {
                    tipo: len(limitacoes) for tipo, limitacoes in estado.limitacoes_conhecidas.items()
                },
                "descobertas_recentes": memoria["descobertas_recentes"][-20:],
                "agentes_mais_ativos": self._obter_agentes_mais_ativos()
            }
            
            return relatorio
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório consolidado: {str(e)}")
            return {}
            
    def _obter_agentes_mais_ativos(self, limite: int = 5) -> List[Dict]:
        """Obtém lista dos agentes mais ativos"""
        try:
            memoria = self._carregar_memoria_coletiva()
            
            agentes = []
            for agente_id, status in memoria["agentes_status"].items():
                agentes.append({
                    "agente_id": agente_id,
                    "sites_descobertos": status.get("sites_descobertos", 0),
                    "total_verificacoes": status.get("total_verificacoes", 0),
                    "ultima_atividade": status.get("ultima_atividade", ""),
                    "status": status.get("status", "inativo")
                })
                
            # Ordenar por total de verificações
            agentes.sort(key=lambda x: x["total_verificacoes"], reverse=True)
            
            return agentes[:limite]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter agentes mais ativos: {str(e)}")
            return []


# Instância global do sistema de memória coletiva
memoria_coletiva = SistemaMemoriaColetiva()


if __name__ == "__main__":
    # Teste básico do sistema
    sistema = SistemaMemoriaColetiva()
    
    # Simular algumas descobertas
    site_teste = {
        "url": "https://exemplo.ai",
        "nome": "Exemplo AI",
        "modelo_detectado": "GPT-Teste",
        "qualidade_resposta": 8,
        "nivel_censura": 3,
        "velocidade_resposta": 2.5,
        "disponibilidade": 9,
        "facilidade_acesso": 7,
        "metadados": {"tipo": "test"}
    }
    
    sistema.registrar_descoberta_site("test_agent_001", site_teste)
    sistema.atualizar_estrategia_eficacia("conversacao_natural", True)
    
    estado = sistema.obter_estado_memoria()
    print(f"Estado atual: {estado}")
    
    relatorio = sistema.gerar_relatorio_consolidado()
    print(f"Sites mapeados: {relatorio['resumo_geral']['total_sites_mapeados']}")