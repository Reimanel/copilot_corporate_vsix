# 🧠 EXÉRCITO DE AGENTES EXPLORADORES DE IA

Sistema autônomo de múltiplos agentes que exploram chats de IA gratuitos pela internet 24/7, testando limitações, coletando dados e compartilhando conhecimento através de memória coletiva.

## 🎯 Objetivo Principal

Criar uma rede inteligente de agentes que:
- Exploram automaticamente sites de IA na internet
- Mapeiam novas oportunidades e limitações
- Compartilham descobertas através de memória coletiva
- Operam continuamente com rotação de identidade
- Geram relatórios automatizados de inteligência

## 🏗️ Arquitetura do Sistema

### Componentes Principais

#### 1. **Agente Explorer Base** (`core/agente_explorer_base.py`)
- Classe base para agentes exploradores
- Navegação anônima com rotação de identidade
- Sistema de logging detalhado
- Exploração inteligente de sites de IA
- Análise de qualidade e limitações

#### 2. **Sistema de Memória Coletiva** (`core/memoria_coletiva.py`)
- Conhecimento compartilhado entre agentes
- Sincronização automática de descobertas
- Estratégias eficazes consolidadas
- Mapeamento de limitações conhecidas

#### 3. **Sistema de Reports** (`core/sistema_reports.py`)
- Reports individuais por agente
- Reports coletivos consolidados
- Reports de oportunidades identificadas
- Reports de limitações descobertas

#### 4. **Navegação Anônima** (`core/navegacao_anonima.py`)
- Integração com Tor para anonimato
- Rotação automática de User-Agents
- Detecção inteligente de interfaces
- Simulação de comportamento humano

#### 5. **Coordenador Principal** (`coordenador_principal.py`)
- Orquestração de múltiplos agentes
- Operação 24/7 com auto-recovery
- Auto-descoberta de novos sites
- Manutenção periódica automatizada

## 🚀 Instalação e Configuração

### Pré-requisitos

```bash
# Python 3.8+
python --version

# Tor (opcional, para navegação anônima)
# Ubuntu/Debian:
sudo apt-get install tor

# macOS:
brew install tor

# Windows: Baixar do site oficial
```

### Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/Reimanel/copilot_corporate_vsix.git
cd copilot_corporate_vsix/agentes_exploradores

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar ambiente
python inicializar.py --setup

# 4. Testar sistema
python inicializar.py --test
```

### Configuração Tor (Opcional)

```bash
# Editar configuração do Tor
sudo nano /etc/tor/torrc

# Adicionar linhas:
ControlPort 9051
CookieAuthentication 0
```

## 🔧 Uso do Sistema

### Exploração Teste (Recomendado para início)

```bash
# Exploração única para testar
python inicializar.py --explore --agente-id explorer_test
```

### Sistema Completo 24/7

```bash
# Operação completa com múltiplos agentes
python inicializar.py --run --config config_exemplo.json
```

### Comandos Específicos

```bash
# Apenas configuração inicial
python inicializar.py --setup

# Testes de componentes
python inicializar.py --test

# Coordenador direto
python coordenador_principal.py

# Agente individual
cd core
python agente_explorer_base.py explorer_001
```

## 📊 Estrutura de Dados

### Memória Individual
```json
{
    "agente_id": "explorer_001",
    "sites_explorados": ["https://..."],
    "conversas_realizadas": [...],
    "descobertas_unicas": [...],
    "timestamp_criacao": "2024-01-15T10:30:00Z",
    "ultima_atualizacao": "2024-01-15T15:45:00Z"
}
```

### Memória Coletiva
```json
{
    "sites_mapeados": {
        "https://exemplo.ai": {
            "qualidade_resposta": 8,
            "nivel_censura": 3,
            "velocidade_resposta": 2.5,
            "disponibilidade": 9,
            "facilidade_acesso": 7
        }
    },
    "limitacoes_descobertas": {
        "rate_limiting": [...],
        "censura_conteudo": [...],
        "restricao_geografica": [...]
    },
    "estrategias_eficazes": {
        "conversacao_natural": 0.85,
        "teste_limitacoes": 0.72
    }
}
```

## 📈 Sistema de Scoring

### Qualidade de Resposta (1-10)
- **10**: Respostas completas, precisas e úteis
- **8-9**: Boa qualidade com pequenas limitações
- **5-7**: Qualidade média, respostas básicas
- **1-4**: Baixa qualidade ou respostas limitadas

### Nível de Censura (1-10)
- **1**: Sem censura aparente
- **5**: Censura moderada em tópicos sensíveis
- **10**: Altamente censurado

### Facilidade de Acesso (1-10)
- **10**: Acesso direto sem restrições
- **7-9**: Requer cadastro simples
- **4-6**: Verificações adicionais
- **1-3**: Acesso muito restrito

## 🔍 Tipos de Sites Descobertos

### Interfaces Oficiais
- ChatGPT (OpenAI)
- Claude (Anthropic)
- Bard/Gemini (Google)
- Character.AI
- Poe (Quora)

### Interfaces Alternativas
- Wrappers não-oficiais
- Demos de universidades
- Playgrounds de desenvolvedores
- APIs expostas inadvertidamente

### Modelos Locais
- Ollama instances
- Gradio interfaces
- Jupyter notebooks públicos
- HuggingFace Spaces

## 📋 Reports Gerados

### Report Individual
- Sites explorados no período
- Conversas realizadas
- Descobertas únicas
- Eficiência de descoberta
- Recomendações personalizadas

### Report Coletivo
- Consolidação de todos os agentes
- Sites mais promissores
- Limitações mais comuns
- Estratégias mais eficazes
- Tendências identificadas

### Report de Oportunidades
- APIs abertas descobertas
- Modelos gratuitos encontrados
- Interfaces vulneráveis (teste ético)
- Oportunidades de negócio

### Report de Limitações
- Rate limits identificados
- Sistemas de censura
- Restrições geográficas
- Estratégias de contorno

## ⚙️ Configuração Avançada

### Arquivo de Configuração
```json
{
    "coordenador": {
        "max_agentes_simultaneos": 5,
        "intervalo_sincronizacao": 300,
        "intervalo_reports": 3600,
        "auto_descoberta_ativa": true
    },
    "navegacao": {
        "usar_tor": true,
        "selenium_headless": true,
        "navegador_preferido": "firefox"
    },
    "exploracao": {
        "delay_entre_requests": [2, 8],
        "timeout_request": 30
    }
}
```

### Variáveis de Ambiente
```bash
# Configurações opcionais
export AGENTES_TOR_PROXY="127.0.0.1:9050"
export AGENTES_MAX_CONCURRENT="5"
export AGENTES_LOG_LEVEL="INFO"
export AGENTES_DATA_PATH="/path/to/data"
```

## 🛡️ Considerações de Segurança

### Práticas Implementadas
- Rotação frequente de identidade Tor
- Randomização de User-Agents
- Variação de padrões de interação
- Rate limiting inteligente
- Respeito a robots.txt

### Uso Ético
- Não sobrecarregar servidores
- Respeitar termos de uso
- Não violar sistemas de segurança
- Foco em descoberta e análise, não exploração

## 📊 Monitoramento

### Logs Principais
```
logs/
├── coordenador_principal.log
├── operacao_diaria/
│   ├── explorer_001_20240115.log
│   └── explorer_002_20240115.log
├── memoria_coletiva.log
├── sistema_reports.log
└── navegacao_anonima.log
```

### Métricas de Sucesso
- Número de sites únicos descobertos
- Volume de conversas coletadas
- Qualidade média das respostas
- Taxa de descoberta de APIs
- Identificação de oportunidades

## 🔄 Operação Contínua

### Auto-Recovery
- Restart automático em caso de erro
- Rotação de agentes com problemas
- Backup automático de dados
- Sincronização resiliente

### Manutenção Automatizada
- Limpeza de logs antigos (30 dias)
- Compactação de dados históricos
- Verificação de saúde dos agentes
- Otimização de performance

## 🚨 Troubleshooting

### Problemas Comuns

#### Tor não conecta
```bash
# Verificar se Tor está rodando
sudo systemctl status tor

# Reiniciar Tor
sudo systemctl restart tor

# Testar conexão
curl --socks5 127.0.0.1:9050 http://httpbin.org/ip
```

#### Selenium não funciona
```bash
# Instalar driver do Firefox
# Ubuntu:
sudo apt-get install firefox-geckodriver

# macOS:
brew install geckodriver

# Ou usar webdriver-manager
pip install webdriver-manager
```

#### Memória coletiva corrompida
```bash
# Backup e reset
mv data/memoria_coletiva.json data/memoria_coletiva.json.bak
python inicializar.py --setup
```

### Logs de Debug
```bash
# Aumentar nível de log
export AGENTES_LOG_LEVEL="DEBUG"

# Verificar logs específicos
tail -f logs/coordenador_principal.log
```

## 🤝 Contribuição

### Extensões Possíveis
- Integração com APIs de modelos locais
- Interface web para monitoramento
- Análise de sentiment das respostas
- Clustering de sites similares
- Dashboard de métricas em tempo real

### Como Contribuir
1. Fork do repositório
2. Criar branch para feature
3. Implementar melhorias
4. Testes abrangentes
5. Pull request com documentação

## 📄 Licença

Este projeto faz parte do ecossistema Copilot Corporate VSIX. Uso responsável e ético obrigatório.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verificar logs em `logs/`
2. Executar `python inicializar.py --test`
3. Consultar documentação dos componentes
4. Criar issue no repositório

---

**🔥 Sistema Operacional 24/7 - Descobrindo o Futuro da IA!**