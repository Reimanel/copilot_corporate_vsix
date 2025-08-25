// 5. webview/script.js
// Este script roda na interface do chat. Ele cuida da interação do usuário
// e da comunicação com a lógica principal da extensão (extension.js).

(function () {
    // @ts-ignore
    const vscode = acquireVsCodeApi();

    const messagesContainer = document.getElementById('messages');
    const promptInput = document.getElementById('prompt-input');
    const sendButton = document.getElementById('send-button');
    const agentSelector = document.getElementById('agent');

    let currentBotMessageElement = null;

    // Função para enviar a mensagem para a extensão
    function sendMessage() {
        const text = promptInput.value;
        if (text.trim() === '') return;

        const agent = agentSelector.value;

        // Adiciona a mensagem do usuário na tela
        addMessage(text, 'user');

        // Desabilita o botão para evitar envios duplicados
        sendButton.disabled = true;
        promptInput.value = '';

        // Envia a mensagem para a lógica principal (extension.js)
        vscode.postMessage({
            command: 'sendMessageToCopilot',
            text: text,
            agent: agent
        });

        // Cria um container para a resposta do bot
        currentBotMessageElement = addMessage('', 'bot');
    }

    // Envia a mensagem ao clicar no botão ou pressionar Enter
    sendButton.addEventListener('click', sendMessage);
    promptInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    // Ouve mensagens vindas da extensão (extension.js)
    window.addEventListener('message', event => {
        const message = event.data;
        switch (message.command) {
            case 'streamResponse':
                if (currentBotMessageElement) {
                    // Adiciona o texto recebido ao elemento da mensagem do bot
                    currentBotMessageElement.innerHTML += message.text;
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
                break;
            case 'endStream':
                // Reabilita o botão de envio e limpa a referência
                sendButton.disabled = false;
                currentBotMessageElement = null;
                // Converte o texto simples em HTML formatado (negrito, listas, etc.)
                // Esta é uma conversão simples, pode ser melhorada com uma lib de Markdown
                formatLastBotMessage();
                break;
            case 'showError':
                addMessage(`ERRO: ${message.text}`, 'system');
                sendButton.disabled = false;
                break;
             case 'addSystemMessage':
                addMessage(message.text, 'system');
                break;
        }
    });

    function addMessage(text, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}-message`;
        messageElement.textContent = text;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return messageElement;
    }

    // Função para formatar a última mensagem do bot
    function formatLastBotMessage() {
        const botMessages = messagesContainer.querySelectorAll('.bot-message');
        if (botMessages.length === 0) return;
        
        const lastBotMessage = botMessages[botMessages.length - 1];
        let content = lastBotMessage.textContent;

        // Regex para encontrar blocos de código e envolvê-los em <pre><code>
        const codeBlockRegex = /```(\w*)\n([\s\S]*?)\n```/g;
        content = content.replace(codeBlockRegex, (match, lang, code) => {
            // Escapa caracteres HTML para segurança
            const escapedCode = code.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            return `<pre><code class="language-${lang}">${escapedCode.trim()}</code></pre>`;
        });
        
        lastBotMessage.innerHTML = content;
    }

}());



