/**
 * AIチャット機能
 */

class ChatManager {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.chatSendBtn = document.getElementById('chat-send-btn');
        this.clearChatBtn = document.getElementById('clear-chat');

        this.initEventListeners();

        this.updateSendButton();
    }

    initEventListeners() {
        // フォーム送信
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // 入力フィールドの状態監視
        this.chatInput.addEventListener('input', () => this.updateSendButton());

        // チャットクリア
        this.clearChatBtn.addEventListener('click', () => this.clearChat());

        // Enterキーでの送信（Shift+Enterは改行、日本語入力中は送信しない）
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
                // 日本語入力変換中でない場合のみ送信
                if (!this.isComposing) {
                    e.preventDefault();
                    this.handleSubmit(e);
                }
            }
        });

        // 日本語入力の変換状態を追跡
        this.isComposing = false;
        this.chatInput.addEventListener('compositionstart', () => {
            this.isComposing = true;
        });
        this.chatInput.addEventListener('compositionend', () => {
            this.isComposing = false;
        });
    }

    updateSendButton() {
        const text = this.chatInput.value;
        const hasText = text.trim().length > 0;
        this.chatSendBtn.disabled = !hasText;
    }

    async handleSubmit(event) {
        event.preventDefault();

        const message = this.chatInput.value.trim();
        if (!message) return;

        // ユーザーメッセージを表示
        this.addMessage(message, 'user');

        // 入力フィールドをクリア
        this.chatInput.value = '';
        this.updateSendButton();

        // 送信ボタンを無効化
        this.chatSendBtn.disabled = true;
        this.chatSendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            // APIに送信
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const result = await response.json();

            if (result.success) {
                // AIの応答を表示
                this.addMessage(result.response, 'ai');

                // 予約が作成された場合、予約表を更新
                if (result.action === 'reserve' && result.reservation) {
                    this.updateReservationTable(result.reservation);
                }

                // キャンセルが実行された場合、予約表を更新
                if (result.action === 'cancel') {
                    this.refreshReservationTable();
                }
            } else {
                this.addMessage(result.response || 'エラーが発生しました', 'ai');
            }

        } catch (error) {
            console.error('チャットエラー:', error);
            this.addMessage('通信エラーが発生しました。もう一度お試しください。', 'ai');
        } finally {
            // 送信ボタンを復元
            this.chatSendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.updateSendButton();
        }
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        if (type === 'ai') {
            messageContent.innerHTML = `<i class="fas fa-robot me-2"></i>${content.replace(/\n/g, '<br>')}`;
        } else {
            messageContent.innerHTML = `<i class="fas fa-user me-2"></i>${content.replace(/\n/g, '<br>')}`;
        }

        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);

        // スクロールを最下部に
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    clearChat() {
        // 初期メッセージ以外を削除
        const messages = this.chatMessages.querySelectorAll('.message');
        messages.forEach((message, index) => {
            if (index > 0) { // 最初のメッセージ（初期メッセージ）は残す
                message.remove();
            }
        });
    }

    updateReservationTable(reservation) {
        // 既存の予約表示機能を使用
        if (window.displayReservationInTable) {
            window.displayReservationInTable(reservation, true);
        }
    }

    refreshReservationTable() {
        // 今日の予約を再読み込み
        if (window.loadTodaysReservations) {
            window.loadTodaysReservations();
        }
    }
}

// チャット機能を初期化
document.addEventListener('DOMContentLoaded', () => {
    new ChatManager();
});

// CSS スタイルを動的に追加
const chatStyles = `
<style>
.chat-card {
    display: flex;
    flex-direction: column;
}

.chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    max-height: 500px;
    padding: 10px;
}

.message {
    margin-bottom: 15px;
}

.message-content {
    padding: 8px 12px;
    border-radius: 8px;
    max-width: 90%;
    word-wrap: break-word;
}

.user-message .message-content {
    background-color: #007bff;
    color: white;
    margin-left: auto;
    margin-right: 0;
    text-align: right;
}

.ai-message .message-content {
    background-color: #f8f9fa;
    color: #333;
    border: 1px solid #dee2e6;
}

.chat-input-container {
    flex-shrink: 0;
}

#chat-input {
    border-radius: 20px;
    padding: 8px 12px;
}

#chat-input:focus {
    border-color: #007bff;
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

#chat-send-btn {
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
}

#chat-send-btn:disabled {
    opacity: 0.6;
}

.chat-messages::-webkit-scrollbar {
    width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>
`;

// スタイルをheadに追加
document.head.insertAdjacentHTML('beforeend', chatStyles);