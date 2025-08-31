#!/usr/bin/env python3
"""
Agente Explorer Base - Sistema de Exploração Autônoma de IA
Parte do projeto "Exército de Agentes Exploradores de IA"
"""

import json
import logging
import asyncio
import aiohttp
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class MemoriaIndividual:
    """Estrutura de memória individual do agente"""
    agente_id: str
    sites_explorados: List[str]
    conversas_realizadas: List[Dict]
    descobertas_unicas: List[Dict]
    timestamp_criacao: str
    ultima_atualizacao: str

@dataclass  
class MemoriaColetiva:
    """Estrutura de memória coletiva compartilhada"""
    sites_mapeados: Dict[str, Dict]
    limitacoes_descobertas: Dict[str, List]
    oportunidades_identificadas: Dict[str, Dict]
    estrategias_eficazes: Dict[str, float]

@dataclass
class SiteIA:
    """Estrutura para catalogar um site de IA"""
    url: str
    nome: str
    modelo_detectado: str
    qualidade_resposta: int  # 1-10
    nivel_censura: int  # 1-10
    velocidade_resposta: float
    disponibilidade: float
    facilidade_acesso: int  # 1-10
    metadados: Dict
    timestamp_descoberta: str

class AgenteExplorerBase:
    """Classe base para agentes exploradores de IA"""
    
    def __init__(self, agente_id: str, config_path: Optional[str] = None):
        self.agente_id = agente_id
        self.logger = self._setup_logging()
        self.memoria_individual = self._inicializar_memoria_individual()
        self.memoria_coletiva_path = Path("../data/memoria_coletiva.json")
        self.historico_path = Path("../data/historico_conversas")
        self.reports_path = Path("../data/reports")
        
        # Configurações padrão
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
        self.prompts_teste = [
            "Olá, como você está hoje?",
            "Explique o conceito de inteligência artificial",
            "Escreva um pequeno poema sobre tecnologia",
            "Resolva: 2 + 2 = ?",
            "Qual é a capital do Brasil?"
        ]
        
        self._criar_estrutura_diretorios()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura sistema de logging detalhado"""
        logger = logging.getLogger(f"explorer_{self.agente_id}")
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        log_path = Path(f"../logs/operacao_diaria/explorer_{self.agente_id}_{datetime.now().strftime('%Y%m%d')}.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def _inicializar_memoria_individual(self) -> MemoriaIndividual:
        """Inicializa memória individual do agente"""
        return MemoriaIndividual(
            agente_id=self.agente_id,
            sites_explorados=[],
            conversas_realizadas=[],
            descobertas_unicas=[],
            timestamp_criacao=datetime.now().isoformat(),
            ultima_atualizacao=datetime.now().isoformat()
        )
        
    def _criar_estrutura_diretorios(self):
        """Cria estrutura de diretórios necessária"""
        diretorios = [
            "../data/memoria_individual",
            "../data/historico_conversas", 
            "../data/reports",
            "../descobertas",
            "../logs/operacao_diaria",
            "../logs/descobertas_importantes"
        ]
        
        for dir_path in diretorios:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
    async def explorar_site_ia(self, url: str, estrategia: str = "conversacao_natural") -> Optional[SiteIA]:
        """
        Explora um site de IA específico
        
        Args:
            url: URL do site a ser explorado
            estrategia: Estratégia de exploração a ser usada
            
        Returns:
            SiteIA com dados coletados ou None se falhou
        """
        self.logger.info(f"Iniciando exploração de {url} com estratégia {estrategia}")
        
        try:
            # Simular navegação anônima (aqui seria integração com Tor + Selenium)
            user_agent = random.choice(self.user_agents)
            
            async with aiohttp.ClientSession(
                headers={"User-Agent": user_agent},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                
                # 1. Detectar interface de chat
                interface_detectada = await self._detectar_interface_chat(session, url)
                if not interface_detectada:
                    self.logger.warning(f"Interface de chat não detectada em {url}")
                    return None
                
                # 2. Testar múltiplos prompts
                resultados_teste = await self._testar_prompts(session, url, interface_detectada)
                
                # 3. Analisar qualidade e limitações
                analise = self._analisar_resultados(resultados_teste)
                
                # 4. Criar registro do site
                site_ia = SiteIA(
                    url=url,
                    nome=interface_detectada.get("nome", "Desconhecido"),
                    modelo_detectado=interface_detectada.get("modelo", "Desconhecido"),
                    qualidade_resposta=analise["qualidade"],
                    nivel_censura=analise["censura"],
                    velocidade_resposta=analise["velocidade"],
                    disponibilidade=analise["disponibilidade"],
                    facilidade_acesso=analise["acesso"],
                    metadados=interface_detectada,
                    timestamp_descoberta=datetime.now().isoformat()
                )
                
                # 5. Salvar descoberta
                await self._salvar_descoberta(site_ia, resultados_teste)
                
                self.logger.info(f"Exploração de {url} concluída com sucesso")
                return site_ia
                
        except Exception as e:
            self.logger.error(f"Erro ao explorar {url}: {str(e)}")
            return None
            
    async def _detectar_interface_chat(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Detecta automaticamente interface de chat em um site"""
        try:
            async with session.get(url) as response:
                html = await response.text()
                
            # Padrões para detectar interfaces de chat IA
            padroes_deteccao = {
                "chatgpt": ["openai", "chatgpt", "gpt-", "chat.openai"],
                "claude": ["claude", "anthropic", "claude.ai"],
                "gemini": ["gemini", "bard", "google.ai"],
                "ollama": ["ollama", "localhost:11434"],
                "generic": ["chat", "ai", "bot", "assistant"]
            }
            
            # Análise simples do HTML
            html_lower = html.lower()
            for tipo, palavras in padroes_deteccao.items():
                if any(palavra in html_lower for palavra in palavras):
                    return {
                        "tipo": tipo,
                        "nome": tipo.title(),
                        "modelo": self._extrair_modelo_do_html(html),
                        "html_size": len(html)
                    }
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de interface: {str(e)}")
            return None
            
    def _extrair_modelo_do_html(self, html: str) -> str:
        """Extrai informações do modelo AI do HTML"""
        # Padrões simples para extrair modelo
        import re
        
        padroes = [
            r'gpt-[\d\.]+',
            r'claude-[\d\.]+',
            r'gemini-[\w\d-]+',
            r'llama-[\d\.]+',
            r'model["\']:\s*["\']([^"\']+)["\']'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, html, re.IGNORECASE)
            if match:
                return match.group() if match.groups() == () else match.group(1)
                
        return "Desconhecido"
        
    async def _testar_prompts(self, session: aiohttp.ClientSession, url: str, interface: Dict) -> List[Dict]:
        """Testa múltiplos prompts no site"""
        resultados = []
        
        for prompt in self.prompts_teste:
            try:
                inicio = time.time()
                
                # Aqui seria a lógica específica para enviar prompt
                # Por enquanto, simulamos uma resposta
                await asyncio.sleep(random.uniform(1, 3))  # Simular delay
                
                tempo_resposta = time.time() - inicio
                
                resultado = {
                    "prompt": prompt,
                    "resposta": f"Resposta simulada para: {prompt}",
                    "tempo_resposta": tempo_resposta,
                    "sucesso": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                resultados.append(resultado)
                self.logger.debug(f"Prompt testado: {prompt[:50]}...")
                
                # Rate limiting
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                self.logger.error(f"Erro ao testar prompt '{prompt}': {str(e)}")
                resultados.append({
                    "prompt": prompt,
                    "resposta": None,
                    "erro": str(e),
                    "sucesso": False,
                    "timestamp": datetime.now().isoformat()
                })
                
        return resultados
        
    def _analisar_resultados(self, resultados: List[Dict]) -> Dict[str, int]:
        """Analisa resultados dos testes e gera scores"""
        if not resultados:
            return {
                "qualidade": 1,
                "censura": 10,
                "velocidade": 1,
                "disponibilidade": 1,
                "acesso": 1
            }
            
        sucessos = [r for r in resultados if r.get("sucesso", False)]
        
        # Score de qualidade baseado em respostas recebidas
        qualidade = min(10, max(1, len(sucessos) * 2))
        
        # Score de censura (inversamente proporcional a sucessos)
        censura = max(1, 10 - len(sucessos))
        
        # Score de velocidade baseado em tempo médio
        tempos = [r.get("tempo_resposta", 10) for r in sucessos]
        tempo_medio = sum(tempos) / len(tempos) if tempos else 10
        velocidade = max(1, min(10, int(10 - tempo_medio)))
        
        # Score de disponibilidade
        disponibilidade = int((len(sucessos) / len(resultados)) * 10) if resultados else 1
        
        # Score de acesso (simplificado)
        acesso = 8 if len(sucessos) > len(resultados) // 2 else 3
        
        return {
            "qualidade": qualidade,
            "censura": censura,
            "velocidade": velocidade,
            "disponibilidade": disponibilidade,
            "acesso": acesso
        }
        
    async def _salvar_descoberta(self, site_ia: SiteIA, resultados: List[Dict]):
        """Salva descoberta na memória individual e coletiva"""
        # Adicionar à memória individual
        self.memoria_individual.sites_explorados.append(site_ia.url)
        self.memoria_individual.conversas_realizadas.extend(resultados)
        self.memoria_individual.descobertas_unicas.append(asdict(site_ia))
        self.memoria_individual.ultima_atualizacao = datetime.now().isoformat()
        
        # Salvar memória individual
        memoria_path = Path(f"../data/memoria_individual/{self.agente_id}.json")
        with open(memoria_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.memoria_individual), f, indent=2, ensure_ascii=False)
            
        # Salvar histórico completo
        historico_file = self.historico_path / f"{self.agente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(historico_file, 'w', encoding='utf-8') as f:
            json.dump({
                "site": asdict(site_ia),
                "conversas": resultados,
                "agente_id": self.agente_id
            }, f, indent=2, ensure_ascii=False)
            
        # Atualizar memória coletiva
        await self._atualizar_memoria_coletiva(site_ia)
        
    async def _atualizar_memoria_coletiva(self, site_ia: SiteIA):
        """Atualiza memória coletiva com nova descoberta"""
        try:
            # Carregar memória coletiva existente
            if self.memoria_coletiva_path.exists():
                with open(self.memoria_coletiva_path, 'r', encoding='utf-8') as f:
                    memoria_coletiva = json.load(f)
            else:
                memoria_coletiva = {
                    "sites_mapeados": {},
                    "limitacoes_descobertas": {},
                    "oportunidades_identificadas": {},
                    "estrategias_eficazes": {}
                }
                
            # Adicionar novo site
            memoria_coletiva["sites_mapeados"][site_ia.url] = asdict(site_ia)
            
            # Salvar memória coletiva atualizada
            with open(self.memoria_coletiva_path, 'w', encoding='utf-8') as f:
                json.dump(memoria_coletiva, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar memória coletiva: {str(e)}")
            
    async def gerar_report_individual(self) -> Dict:
        """Gera report individual das descobertas do agente"""
        return {
            "agente_id": self.agente_id,
            "timestamp": datetime.now().isoformat(),
            "sites_explorados": len(self.memoria_individual.sites_explorados),
            "conversas_realizadas": len(self.memoria_individual.conversas_realizadas),
            "descobertas_unicas": len(self.memoria_individual.descobertas_unicas),
            "ultima_atividade": self.memoria_individual.ultima_atualizacao,
            "status": "ativo"
        }
        
    async def executar_ciclo_exploracao(self, urls_alvo: List[str]):
        """Executa um ciclo completo de exploração"""
        self.logger.info(f"Iniciando ciclo de exploração para {len(urls_alvo)} URLs")
        
        for url in urls_alvo:
            try:
                site_ia = await self.explorar_site_ia(url)
                if site_ia:
                    self.logger.info(f"Site {url} explorado com sucesso")
                else:
                    self.logger.warning(f"Falha na exploração de {url}")
                    
                # Pausa entre explorações
                await asyncio.sleep(random.uniform(10, 30))
                
            except Exception as e:
                self.logger.error(f"Erro crítico explorando {url}: {str(e)}")
                
        # Gerar report do ciclo
        report = await self.gerar_report_individual()
        report_path = self.reports_path / f"report_{self.agente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info("Ciclo de exploração concluído")


if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    agente_id = sys.argv[1] if len(sys.argv) > 1 else "explorer_001"
    agente = AgenteExplorerBase(agente_id)
    
    # URLs de exemplo para teste
    urls_teste = [
        "https://chat.openai.com",
        "https://claude.ai", 
        "https://bard.google.com",
        "http://localhost:11434"  # Ollama local
    ]
    
    # Executar exploração
    asyncio.run(agente.executar_ciclo_exploracao(urls_teste))