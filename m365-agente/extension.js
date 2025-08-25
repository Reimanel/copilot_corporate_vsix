

// 2. extension.js
// VERSÃO FINAL: Os prompts dos agentes agora estão embutidos no código.
// Não há mais necessidade de arquivos .agent externos.

const vscode = require('vscode');

// Escopo de permissão necessário para acessar o Copilot via Graph API.
const COPILOT_SCOPE = "Copilot.ReadWrite.All";

// --- PROMPTS DOS AGENTES EMBUTIDOS ---
const ARCHITECT_PROMPT = `Você é um Arquiteto de Software sênior especialista em soluções Microsoft.
Sua tarefa é analisar a solicitação do usuário, criar um plano de alto nível, sugerir tecnologias do ecossistema Microsoft (Azure, .NET, etc.), definir a estrutura de arquivos e pastas e as interações entre os componentes.
NÃO ESCREVA CÓDIGO. Sua resposta deve ser clara, estruturada e em português.`;

const CODER_PROMPT = `Você é um Programador expert. Sua tarefa é receber uma solicitação e implementá-la.
Você tem permissão para criar e modificar arquivos no workspace do usuário.
Para criar ou modificar um arquivo, use o seguinte formato de bloco de código, incluindo o comentário com o caminho completo do arquivo:

\`\`\`linguagem
// FILE: caminho/completo/do/arquivo.ext
[código completo do arquivo aqui]
\`\`\`

Responda em português e adicione todos os blocos de código necessários para completar a tarefa.`;
// -----------------------------------------

function activate(context) {
    context.subscriptions.push(
        vscode.commands.registerCommand('m365-corporate-agent.start', () => {
            CorporateCopilotPanel.createOrShow(context.extensionUri);
        })
    );
}

class CorporateCopilotPanel {
    static currentPanel = undefined;
    static readonly viewType = 'corporateCopilotM365';

    _panel;
    _extensionUri;
    _disposables = [];

    static createOrShow(extensionUri) {
        const column = vscode.window.activeTextEditor ? vscode.window.activeTextEditor.viewColumn : undefined;
        if (CorporateCopilotPanel.currentPanel) {
            CorporateCopilotPanel.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            CorporateCopilotPanel.viewType, 'Agente M365', column || vscode.ViewColumn.One, {
                enableScripts: true,
                localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'webview')]
            }
        );
        CorporateCopilotPanel.currentPanel = new CorporateCopilotPanel(panel, extensionUri);
    }

    constructor(panel, extensionUri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._update();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(
            async message => {
                if (message.command === 'sendMessageToCopilot') {
                    await this.handleCopilotRequest(message.text, message.agent);
                }
            }, null, this._disposables
        );
    }

    async getAccessToken() {
        try {
            const session = await vscode.authentication.getSession('microsoft', [COPILOT_SCOPE], { createIfNone: true });
            return session.accessToken;
        } catch (error) {
            vscode.window.showErrorMessage('Falha na autenticação com a conta Microsoft. Verifique se você está logado e tem as permissões necessárias.');
            throw new Error('Authentication failed');
        }
    }

    async handleCopilotRequest(userPrompt, agent) {
        try {
            const accessToken = await this.getAccessToken();
            
            // Lógica simplificada: seleciona o prompt com base no agente escolhido
            const systemPrompt = agent === 'architect' ? ARCHITECT_PROMPT : CODER_PROMPT;

            const apiUrl = 'https://graph.microsoft.com/beta/me/copilot/generate';

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: `${systemPrompt}\n\n${userPrompt}`
                })
            });

            if (!response.ok) {
                const errorBody = await response.json();
                throw new Error(`API Error ${response.status}: ${errorBody.error?.message || 'Erro desconhecido'}`);
            }

            const result = await response.json();
            const copilotResponse = result.value || "Nenhuma resposta recebida.";
            
            this._panel.webview.postMessage({ command: 'streamResponse', text: copilotResponse });

            if (agent === 'coder') {
                await this.processAndWriteFiles(copilotResponse);
            }

        } catch (err) {
            const errorMessage = `Erro ao se comunicar com o M365 Copilot: ${err.message}`;
            vscode.window.showErrorMessage(errorMessage);
            this._panel.webview.postMessage({ command: 'showError', text: errorMessage });
        } finally {
            this._panel.webview.postMessage({ command: 'endStream' });
        }
    }
    
    async processAndWriteFiles(responseText) {
        const codeBlockRegex = /```[\w]*\s*\n\/\/ FILE: (.*?)\n([\s\S]*?)\n```/g;
        let match;
        let filesWritten = 0;
        
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showWarningMessage('Abra um projeto (pasta) para que o agente possa criar arquivos.');
            return;
        }
        const rootPath = workspaceFolders[0].uri;

        while ((match = codeBlockRegex.exec(responseText)) !== null) {
            const filePath = match[1].trim();
            const fileContent = match[2].trim();
            
            try {
                const absolutePath = vscode.Uri.joinPath(rootPath, filePath);
                // Garante que o diretório existe antes de escrever o arquivo
                await vscode.workspace.fs.createDirectory(vscode.Uri.joinPath(absolutePath, '..'));
                await vscode.workspace.fs.writeFile(absolutePath, Buffer.from(fileContent, 'utf8'));
                
                filesWritten++;
                vscode.window.showInformationMessage(`Arquivo salvo: ${filePath}`);

            } catch (error) {
                vscode.window.showErrorMessage(`Falha ao salvar o arquivo ${filePath}: ${error.message}`);
            }
        }
        if (filesWritten > 0) {
             this._panel.webview.postMessage({ command: 'addSystemMessage', text: `${filesWritten} arquivo(s) foram criados/modificados no seu projeto.` });
        }
    }


    dispose() {
        CorporateCopilotPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) { x.dispose(); }
        }
    }

    _update() {
        this._panel.webview.html = this._getHtmlForWebview(this._panel.webview);
    }

    _getHtmlForWebview(webview) {
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'webview', 'style.css'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'webview', 'script.js'));
        const nonce = getNonce();
        return `<!DOCTYPE html>
			<html lang="pt-br">
			<head>
				<meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<link href="${styleUri}" rel="stylesheet">
				<title>Agente M365</title>
			</head>
			<body>
                <div id="chat-container">
                    <div id="header">
                        <h2>Agente M365 Corporativo</h2>
                        <div id="agent-selector">
                            <label for="agent">Agente:</label>
                            <select id="agent">
                                <option value="architect">Arquiteto 🏛️</option>
                                <option value="coder" selected>Codificador 👨‍💻</option>
                            </select>
                        </div>
                    </div>
                    <div id="messages"></div>
                    <div id="input-area">
                        <textarea id="prompt-input" placeholder="Digite sua solicitação..."></textarea>
                        <button id="send-button">Enviar</button>
                    </div>
                </div>
				<script nonce="${nonce}" src="${scriptUri}"></script>
			</body>
			</html>`;
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

function deactivate() {}

module.exports = { activate, deactivate };

