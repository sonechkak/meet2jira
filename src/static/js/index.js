// DOM элементы
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadBtn = document.getElementById('uploadBtn');
const uploadIcon = document.getElementById('uploadIcon');
const uploadText = document.getElementById('uploadText');
const processingIndicator = document.getElementById('processingIndicator');
const message = document.getElementById('message');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');

let isProcessing = false;

// Конфигурация
const CONFIG = {
    allowedTypes: [
        'text/plain', 'text/markdown', 'text/x-markdown',
        'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp'
    ],
    allowedExtensions: ['.txt', '.md', '.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
    fileIcons: {
        '.pdf': '📕',
        '.docx': '📘',
        '.txt': '📝',
        '.md': '📋',
        'image': '🖼️',
        'default': '📄'
    }
};

// Утилиты
const Utils = {
    getErrorMessage(error) {
        if (typeof error === 'string') return error;
        if (error?.message) return error.message;
        if (error?.detail) {
            if (typeof error.detail === 'string') return error.detail;
            if (Array.isArray(error.detail)) {
                return error.detail.map(err => {
                    const field = err.loc ? err.loc.join('.') : 'field';
                    const message = err.msg || err.message || 'validation error';
                    return `${field}: ${message}`;
                }).join('; ');
            }
            return JSON.stringify(error.detail, null, 2);
        }
        return 'Неизвестная ошибка';
    },

    getFileIcon(fileName) {
        const name = fileName.toLowerCase();
        if (name.endsWith('.pdf')) return CONFIG.fileIcons['.pdf'];
        if (name.endsWith('.docx')) return CONFIG.fileIcons['.docx'];
        if (name.endsWith('.txt')) return CONFIG.fileIcons['.txt'];
        if (name.endsWith('.md')) return CONFIG.fileIcons['.md'];
        if (name.match(/\.(jpg|jpeg|png|tiff|bmp)$/)) return CONFIG.fileIcons['image'];
        return CONFIG.fileIcons['default'];
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    isValidFile(file) {
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        return CONFIG.allowedTypes.includes(file.type) || CONFIG.allowedExtensions.includes(fileExtension);
    },

    formatContent(content) {
        if (Array.isArray(content)) return content.join('\n');
        if (typeof content === 'object' && content !== null) return JSON.stringify(content, null, 2);
        return content;
    }
};

// UI управление
const UI = {
    setProcessingState(processing) {
        isProcessing = processing;

        if (processing) {
            uploadArea.classList.add('processing');
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Обработка...';
            uploadIcon.textContent = '⏳';
            uploadText.textContent = 'Обрабатываем ваш документ...';
            processingIndicator.style.display = 'block';
        } else {
            uploadArea.classList.remove('processing');
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Выбрать файл';
            uploadIcon.textContent = '📄';
            uploadText.textContent = 'Перетащите документ или изображение сюда или выберите файл';
            processingIndicator.style.display = 'none';
        }
    },

    showMessage(text, type) {
        message.innerHTML = `<div class="message ${type}">${text}</div>`;
        setTimeout(() => {
            if (type !== 'error') {
                this.clearMessage();
            }
        }, 5000);
    },

    clearMessage() {
        message.innerHTML = '';
    },

    showResult(result) {
        const fileIcon = Utils.getFileIcon(result.document_name);
        const summaryContent = Utils.formatContent(result.summary);
        const resultId = `result-${Date.now()}`;
        const summaryId = `summary-${Date.now()}`;

        // Формируем блок с результатами Jira
        let jiraHTML = '';
        if (result.jira_result) {
            if (result.jira_result.success && result.jira_result.created_tasks?.length > 0) {
                jiraHTML = `
                    <div class="jira-success">
                        <h4>✅ Задачи созданы в Jira:</h4>
                        <div class="jira-tasks-list">
                            ${result.jira_result.created_tasks.map(task => `
                                <div class="jira-task-item">
                                    <a href="${task.url}" target="_blank" class="jira-task-link">
                                        🎯 ${task.key}: ${Utils.escapeHtml(task.title)}
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            if (result.jira_result.errors?.length > 0) {
                jiraHTML += `
                    <div class="jira-warnings">
                        <h4>⚠️ Предупреждения:</h4>
                        <ul>${result.jira_result.errors.map(error => `<li>${Utils.escapeHtml(error)}</li>`).join('')}</ul>
                    </div>
                `;
            }
        }

        const resultHTML = `
            <div class="result-card" id="${resultId}">
                <div class="result-header">
                    <div class="document-name">${fileIcon} ${Utils.escapeHtml(result.document_name)}</div>
                    <div class="model-badge">🤖 ${result.model}</div>
                </div>
                
                <div class="summary-label">Найденные задачи:</div>
                <div class="summary-content" id="${summaryId}">
                    ${Utils.escapeHtml(summaryContent).replace(/\n/g, '<br>')}
                </div>
                
                ${jiraHTML}
                
                <div class="action-buttons">
                    <button class="copy-btn" onclick="Actions.copySummary('${summaryId}')">
                        📋 Копировать задачи
                    </button>
                    <button class="feedback-btn accept-btn" onclick="Actions.giveFeedback('${resultId}', 'accept')">
                        👍 Хороший результат
                    </button>
                    <button class="feedback-btn reject-btn" onclick="Actions.giveFeedback('${resultId}', 'reject')">
                        👎 Плохой результат
                    </button>
                </div>
                
                <div class="status-indicator" id="status-${resultId}" style="display: none;"></div>
            </div>
        `;

        resultsList.innerHTML = resultHTML + resultsList.innerHTML;
        resultsSection.style.display = 'block';

        setTimeout(() => {
            resultsSection.scrollIntoView({behavior: 'smooth', block: 'start'});
        }, 100);
    }
};

// Основные действия
const Actions = {
    async processFile() {
        const file = fileInput.files[0];
        if (!file) return;

        if (!Utils.isValidFile(file)) {
            UI.showMessage('Неподдерживаемый формат файла. Используйте PDF, DOCX, TXT, MD или изображения (JPG, PNG, TIFF, BMP).', 'error');
            return;
        }

        UI.setProcessingState(true);
        UI.clearMessage();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/file/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                UI.showResult(result);

                // Определяем сообщение в зависимости от результата Jira
                if (result.jira_result?.success && result.jira_result?.created_tasks?.length > 0) {
                    UI.showMessage('Документ обработан и задачи созданы в Jira!', 'success');
                } else if (result.jira_result?.errors?.length > 0) {
                    UI.showMessage('Документ обработан, но возникли проблемы с созданием задач в Jira', 'warning');
                } else {
                    UI.showMessage('Документ успешно обработан!', 'success');
                }
            } else {
                throw new Error(Utils.getErrorMessage(result));
            }
        } catch (error) {
            UI.showMessage(`Ошибка: ${Utils.getErrorMessage(error)}`, 'error');
            console.error('Processing error:', error);
        } finally {
            UI.setProcessingState(false);
            fileInput.value = '';
        }
    },

    copySummary(elementId) {
        const element = document.getElementById(elementId);
        const text = element.textContent || element.innerText;

        navigator.clipboard.writeText(text).then(() => {
            UI.showMessage('Задачи скопированы в буфер обмена!', 'success');
        }).catch(() => {
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            UI.showMessage('Задачи скопированы в буфер обмена!', 'success');
        });
    },

    async giveFeedback(resultId, feedbackType) {
        const resultCard = document.getElementById(resultId);
        const buttons = resultCard.querySelectorAll('.feedback-btn');
        const targetButton = resultCard.querySelector(`.${feedbackType}-btn`);

        // Показываем загрузку
        targetButton.innerHTML = feedbackType === 'accept' ? '⏳ Отправка...' : '⏳ Отправка...';
        buttons.forEach(btn => btn.disabled = true);

        try {
            const endpoint = feedbackType === 'accept' ? '/file/accept' : '/file/reject';

            // Получаем текст задач для отправки
            const summaryElement = resultCard.querySelector('.summary-content');
            const tasksText = summaryElement ? (summaryElement.textContent || summaryElement.innerText) : '';

            // Единая структура данных для обоих endpoint'ов
            const requestData = {
                result_id: resultId,
                tasks_text: tasksText,  // Добавляем для обоих случаев
                feedback_type: feedbackType,
                timestamp: new Date().toISOString()
            };

            // Для reject добавляем причину
            if (feedbackType === 'reject') {
                requestData.reason = 'Результат отклонен пользователем';
            }

            console.log('Отправляем обратную связь:', requestData);

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            console.log('Ответ сервера:', result);

            if (response.ok && result.success) {
                targetButton.innerHTML = feedbackType === 'accept' ? '✅ Спасибо!' : '❌ Учтено';
                targetButton.style.opacity = '0.7';

                // Добавляем визуальный статус
                resultCard.classList.add(feedbackType === 'accept' ? 'feedback-positive' : 'feedback-negative');

                UI.showMessage(result.message || 'Спасибо за обратную связь!', 'success');
            } else {
                throw new Error(Utils.getErrorMessage(result) || 'Ошибка отправки обратной связи');
            }
        } catch (error) {
            console.error('Feedback error:', error);

            // Возвращаем кнопку в исходное состояние
            targetButton.innerHTML = feedbackType === 'accept' ? '👍 Хороший результат' : '👎 Плохой результат';
            buttons.forEach(btn => btn.disabled = false);

            UI.showMessage(`Ошибка обратной связи: ${Utils.getErrorMessage(error)}`, 'error');
        }
    }
};

// Drag & Drop обработчики
const DragDrop = {
    handleDragOver(e) {
        e.preventDefault();
        if (!isProcessing) {
            uploadArea.classList.add('dragover');
        }
    },

    handleDragLeave(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    },

    handleDrop(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (isProcessing) return;

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            Actions.processFile();
        }
    }
};

// Инициализация событий
function initializeEventListeners() {
    fileInput.addEventListener('change', Actions.processFile);
    uploadArea.addEventListener('dragover', DragDrop.handleDragOver);
    uploadArea.addEventListener('dragleave', DragDrop.handleDragLeave);
    uploadArea.addEventListener('drop', DragDrop.handleDrop);
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', initializeEventListeners);