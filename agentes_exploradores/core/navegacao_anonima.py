#!/usr/bin/env python3
"""
Sistema de Navegação Anônima - Tor + Selenium para Agentes Exploradores
Fornece navegação segura e anônima para exploração de sites de IA
"""

import asyncio
import random
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium não disponível. Modo simulação ativo.")

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

@dataclass
class ConfigNavegacao:
    """Configurações para navegação anônima"""
    usar_tor: bool = True
    tor_proxy_host: str = "127.0.0.1"
    tor_proxy_port: int = 9050
    rotar_identidade_a_cada: int = 5  # requests
    timeout_request: int = 30
    delay_entre_requests: tuple = (2, 8)  # min, max segundos
    user_agents_rotativos: bool = True
    selenium_headless: bool = True
    navegador_preferido: str = "firefox"  # firefox, chrome

class NavegacaoAnonima:
    """Sistema de navegação anônima com Tor e Selenium"""
    
    def __init__(self, config: ConfigNavegacao = None):
        self.config = config or ConfigNavegacao()
        self.logger = self._setup_logging()
        self.session = None
        self.driver = None
        self.request_count = 0
        self.user_agents = self._carregar_user_agents()
        self.proxies = self._configurar_proxies()
        
        # Status da conexão Tor
        self.tor_disponivel = self._verificar_tor()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para navegação"""
        logger = logging.getLogger("navegacao_anonima")
        logger.setLevel(logging.INFO)
        
        log_path = Path("../logs/navegacao_anonima.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def _carregar_user_agents(self) -> List[str]:
        """Carrega lista de User-Agents para rotação"""
        return [
            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Chrome macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Firefox Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            
            # Firefox macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            
            # Safari macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            
            # Edge Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        
    def _configurar_proxies(self) -> Dict:
        """Configura proxies para Tor"""
        if self.config.usar_tor:
            return {
                'http': f'socks5://{self.config.tor_proxy_host}:{self.config.tor_proxy_port}',
                'https': f'socks5://{self.config.tor_proxy_host}:{self.config.tor_proxy_port}'
            }
        return {}
        
    def _verificar_tor(self) -> bool:
        """Verifica se Tor está disponível"""
        if not self.config.usar_tor:
            return False
            
        try:
            # Tentar conectar ao proxy Tor
            test_session = requests.Session()
            test_session.proxies = self.proxies
            test_session.timeout = 10
            
            # Teste simples de conexão
            response = test_session.get("http://httpbin.org/ip", timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Tor detectado e funcional")
                return True
            else:
                self.logger.warning("Tor não está respondendo corretamente")
                return False
                
        except Exception as e:
            self.logger.warning(f"Tor não disponível: {str(e)}")
            return False
            
    def _obter_user_agent_aleatorio(self) -> str:
        """Obtém User-Agent aleatório"""
        if self.config.user_agents_rotativos:
            return random.choice(self.user_agents)
        return self.user_agents[0]
        
    def _delay_aleatorio(self):
        """Aplica delay aleatório entre requests"""
        min_delay, max_delay = self.config.delay_entre_requests
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def _rotar_identidade_tor(self):
        """Rotaciona identidade Tor (nova rota)"""
        if not self.tor_disponivel:
            return
            
        try:
            # Enviar sinal para rotacionar identidade
            # Nota: Requer configuração específica do Tor
            import socket
            
            # Conectar ao control port do Tor (padrão 9051)
            try:
                control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                control_socket.connect(("127.0.0.1", 9051))
                control_socket.send(b"AUTHENTICATE\r\n")
                control_socket.send(b"SIGNAL NEWNYM\r\n")
                control_socket.send(b"QUIT\r\n")
                control_socket.close()
                
                self.logger.info("Identidade Tor rotacionada")
                time.sleep(2)  # Aguardar rotação
                
            except Exception as e:
                self.logger.warning(f"Não foi possível rotacionar identidade Tor: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Erro na rotação de identidade: {str(e)}")
            
    def inicializar_session(self) -> requests.Session:
        """Inicializa session HTTP com configurações anônimas"""
        if self.session:
            self.session.close()
            
        self.session = requests.Session()
        
        # Configurar proxies
        if self.tor_disponivel and self.config.usar_tor:
            self.session.proxies = self.proxies
            
        # Configurar headers
        self.session.headers.update({
            'User-Agent': self._obter_user_agent_aleatorio(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configurar timeout
        self.session.timeout = self.config.timeout_request
        
        self.logger.info("Session HTTP inicializada")
        return self.session
        
    def inicializar_selenium_driver(self) -> Optional[webdriver.Remote]:
        """Inicializa driver Selenium com configurações anônimas"""
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium não disponível")
            return None
            
        try:
            if self.driver:
                self.driver.quit()
                
            # Configurar opções baseado no navegador
            if self.config.navegador_preferido == "chrome":
                options = ChromeOptions()
                
                if self.config.selenium_headless:
                    options.add_argument("--headless")
                    
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # User agent
                options.add_argument(f"--user-agent={self._obter_user_agent_aleatorio()}")
                
                # Proxy Tor
                if self.tor_disponivel and self.config.usar_tor:
                    options.add_argument(f"--proxy-server=socks5://{self.config.tor_proxy_host}:{self.config.tor_proxy_port}")
                    
                self.driver = webdriver.Chrome(options=options)
                
            else:  # Firefox
                options = FirefoxOptions()
                
                if self.config.selenium_headless:
                    options.add_argument("--headless")
                    
                # Profile customizado
                profile = webdriver.FirefoxProfile()
                
                # User agent
                profile.set_preference("general.useragent.override", self._obter_user_agent_aleatorio())
                
                # Proxy Tor
                if self.tor_disponivel and self.config.usar_tor:
                    profile.set_preference("network.proxy.type", 1)
                    profile.set_preference("network.proxy.socks", self.config.tor_proxy_host)
                    profile.set_preference("network.proxy.socks_port", self.config.tor_proxy_port)
                    profile.set_preference("network.proxy.socks_version", 5)
                    
                # Configurações de privacidade
                profile.set_preference("privacy.trackingprotection.enabled", True)
                profile.set_preference("dom.webdriver.enabled", False)
                profile.set_preference('useAutomationExtension', False)
                
                options.profile = profile
                self.driver = webdriver.Firefox(options=options)
                
            # Configurações adicionais
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info(f"Driver Selenium ({self.config.navegador_preferido}) inicializado")
            return self.driver
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar driver Selenium: {str(e)}")
            return None
            
    async def requisicao_http_anonima(self, url: str, metodo: str = "GET", dados: Dict = None, headers: Dict = None) -> Optional[requests.Response]:
        """Faz requisição HTTP anônima"""
        try:
            # Verificar se precisa rotacionar identidade
            if self.request_count >= self.config.rotar_identidade_a_cada:
                self._rotar_identidade_tor()
                self.request_count = 0
                
            # Inicializar session se necessário
            if not self.session:
                self.inicializar_session()
                
            # Atualizar User-Agent
            if self.config.user_agents_rotativos:
                self.session.headers['User-Agent'] = self._obter_user_agent_aleatorio()
                
            # Headers adicionais
            if headers:
                self.session.headers.update(headers)
                
            # Delay antes da requisição
            self._delay_aleatorio()
            
            # Fazer requisição
            if metodo.upper() == "GET":
                response = self.session.get(url)
            elif metodo.upper() == "POST":
                response = self.session.post(url, json=dados)
            else:
                raise ValueError(f"Método HTTP {metodo} não suportado")
                
            self.request_count += 1
            
            self.logger.info(f"Requisição {metodo} para {url}: {response.status_code}")
            return response
            
        except Exception as e:
            self.logger.error(f"Erro na requisição para {url}: {str(e)}")
            return None
            
    async def navegacao_selenium_anonima(self, url: str, aguardar_elemento: str = None, timeout: int = 10) -> Optional[str]:
        """Navega usando Selenium de forma anônima"""
        try:
            # Inicializar driver se necessário
            if not self.driver:
                self.inicializar_selenium_driver()
                
            if not self.driver:
                return None
                
            # Verificar rotação de identidade
            if self.request_count >= self.config.rotar_identidade_a_cada:
                self._rotar_identidade_tor()
                self.inicializar_selenium_driver()  # Reinicializar driver
                self.request_count = 0
                
            # Delay antes da navegação
            self._delay_aleatorio()
            
            # Navegar para URL
            self.driver.get(url)
            
            # Aguardar elemento específico se fornecido
            if aguardar_elemento:
                wait = WebDriverWait(self.driver, timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, aguardar_elemento)))
                
            # Simular comportamento humano
            await self._simular_comportamento_humano()
            
            self.request_count += 1
            
            page_source = self.driver.page_source
            self.logger.info(f"Navegação Selenium para {url} concluída")
            
            return page_source
            
        except TimeoutException:
            self.logger.warning(f"Timeout aguardando elemento em {url}")
            return self.driver.page_source if self.driver else None
            
        except Exception as e:
            self.logger.error(f"Erro na navegação Selenium para {url}: {str(e)}")
            return None
            
    async def _simular_comportamento_humano(self):
        """Simula comportamento humano no navegador"""
        try:
            if not self.driver:
                return
                
            # Simular scroll aleatório
            scroll_pause = random.uniform(0.5, 2.0)
            await asyncio.sleep(scroll_pause)
            
            # Scroll para baixo
            self.driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * 500) + 200);")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Scroll para cima ocasionalmente
            if random.random() < 0.3:
                self.driver.execute_script("window.scrollTo(0, 0);")
                await asyncio.sleep(random.uniform(0.5, 1.0))
                
            # Movimento de mouse aleatório (se possível)
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                
                # Mover mouse para posição aleatória
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
                actions.perform()
                
            except Exception:
                pass  # Ignorar se não conseguir mover mouse
                
        except Exception as e:
            self.logger.debug(f"Erro na simulação de comportamento: {str(e)}")
            
    def obter_informacoes_conexao(self) -> Dict:
        """Obtém informações sobre a conexão atual"""
        try:
            # Verificar IP atual
            if self.session:
                response = self.session.get("http://httpbin.org/ip", timeout=10)
                ip_info = response.json()
            else:
                session_temp = requests.Session()
                if self.tor_disponivel:
                    session_temp.proxies = self.proxies
                response = session_temp.get("http://httpbin.org/ip", timeout=10)
                ip_info = response.json()
                session_temp.close()
                
            return {
                "ip_atual": ip_info.get("origin", "Desconhecido"),
                "tor_ativo": self.tor_disponivel and self.config.usar_tor,
                "user_agent_atual": self.session.headers.get('User-Agent') if self.session else "Não definido",
                "request_count": self.request_count,
                "proxies_configurados": bool(self.proxies)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações de conexão: {str(e)}")
            return {
                "ip_atual": "Erro",
                "tor_ativo": False,
                "user_agent_atual": "Erro",
                "request_count": self.request_count,
                "proxies_configurados": False
            }
            
    def finalizar(self):
        """Finaliza recursos de navegação"""
        try:
            if self.session:
                self.session.close()
                self.session = None
                
            if self.driver:
                self.driver.quit()
                self.driver = None
                
            self.logger.info("Recursos de navegação finalizados")
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar recursos: {str(e)}")
            
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.finalizar()


# Classe utilitária para detecção de interfaces de chat
class DetectorInterfaceChat:
    """Detector especializado para interfaces de chat de IA"""
    
    def __init__(self, navegacao: NavegacaoAnonima):
        self.navegacao = navegacao
        self.logger = logging.getLogger("detector_interface")
        
    async def detectar_tipo_interface(self, url: str) -> Optional[Dict]:
        """Detecta tipo de interface de chat"""
        try:
            # Primeiro tentar com requisição HTTP simples
            response = await self.navegacao.requisicao_http_anonima(url)
            
            if response and response.status_code == 200:
                html = response.text
                return self._analisar_html_interface(html, url)
                
            # Se falhou, tentar com Selenium
            html = await self.navegacao.navegacao_selenium_anonima(url)
            if html:
                return self._analisar_html_interface(html, url)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de interface para {url}: {str(e)}")
            return None
            
    def _analisar_html_interface(self, html: str, url: str) -> Dict:
        """Analisa HTML para identificar tipo de interface"""
        html_lower = html.lower()
        
        # Padrões de detecção
        padroes = {
            "openai": {
                "palavras": ["openai", "chatgpt", "gpt-", "chat.openai"],
                "elementos": ["chatgpt", "openai-chat", "conversation"],
                "tipo": "ChatGPT"
            },
            "anthropic": {
                "palavras": ["anthropic", "claude", "claude.ai"],
                "elementos": ["claude", "anthropic-chat"],
                "tipo": "Claude"
            },
            "google": {
                "palavras": ["bard", "gemini", "google.ai"],
                "elementos": ["bard-chat", "gemini"],
                "tipo": "Bard/Gemini"
            },
            "character": {
                "palavras": ["character.ai", "character"],
                "elementos": ["character-chat"],
                "tipo": "Character.AI"
            },
            "poe": {
                "palavras": ["poe.com", "quora", "poe"],
                "elementos": ["poe-chat"],
                "tipo": "Poe"
            },
            "ollama": {
                "palavras": ["ollama", "localhost:11434"],
                "elementos": ["ollama-ui"],
                "tipo": "Ollama"
            },
            "generic": {
                "palavras": ["chat", "ai", "bot", "assistant", "artificial intelligence"],
                "elementos": ["chat-input", "message-input", "conversation"],
                "tipo": "Generic AI Chat"
            }
        }
        
        for categoria, config in padroes.items():
            # Verificar palavras-chave
            palavras_encontradas = sum(1 for palavra in config["palavras"] if palavra in html_lower)
            
            # Verificar elementos comuns
            elementos_encontrados = sum(1 for elemento in config["elementos"] if elemento in html_lower)
            
            score = palavras_encontradas + elementos_encontradas
            
            if score > 0:
                return {
                    "categoria": categoria,
                    "tipo": config["tipo"],
                    "score_deteccao": score,
                    "url": url,
                    "elementos_encontrados": elementos_encontrados,
                    "palavras_encontradas": palavras_encontradas,
                    "timestamp": datetime.now().isoformat()
                }
                
        # Se nada foi detectado
        return {
            "categoria": "desconhecido",
            "tipo": "Interface Não Identificada",
            "score_deteccao": 0,
            "url": url,
            "elementos_encontrados": 0,
            "palavras_encontradas": 0,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Teste do sistema de navegação anônima
    async def teste_navegacao():
        config = ConfigNavegacao(
            usar_tor=False,  # Desabilitar Tor para teste
            selenium_headless=True
        )
        
        async with NavegacaoAnonima(config) as nav:
            # Teste de requisição HTTP
            response = await nav.requisicao_http_anonima("http://httpbin.org/ip")
            if response:
                print(f"IP atual: {response.json()}")
                
            # Teste de detecção de interface
            detector = DetectorInterfaceChat(nav)
            interface = await detector.detectar_tipo_interface("https://example.com")
            print(f"Interface detectada: {interface}")
            
            # Informações de conexão
            info = nav.obter_informacoes_conexao()
            print(f"Info de conexão: {info}")
            
    asyncio.run(teste_navegacao())