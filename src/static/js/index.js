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
        'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/x-m4a',
        'audio/ogg', 'audio/x-flac', 'audio/flac'
    ],
    allowedExtensions: [
        '.txt', '.md', '.pdf', '.docx',
        '.jpg', '.jpeg', '.png', '.tiff', '.bmp',
        '.mp3', '.wav', '.m4a', '.ogg', '.flac'
    ],
    fileIcons: {
        '.pdf': '📕',
        '.docx': '📘',
        '.txt': '📝',
        '.md': '📋',
        '.mp3': '🎵',
        '.wav': '🎶',
        '.m4a': '🎤',
        '.ogg': '🎧',
        '.flac': '🎼',
        'image': '🖼️',
        'default': '📄',
        'error': '❗',
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

        // Формируем блок для будущих результатов Jira (пока пустой)
        const jiraHTML = `
            <div class="jira-placeholder" id="jira-${resultId}" style="display: none;">
                <!-- Результаты Jira появятся здесь после нажатия "Хороший результат" -->
            </div>
        `;

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
                    <button class="feedback-btn accept-btn" onclick="Actions.createJiraTasks('${resultId}')">
                        ✅ Хороший результат - создать задачи в Jira
                    </button>
                    <button class="feedback-btn reject-btn" onclick="Actions.giveFeedback('${resultId}', 'reject')">
                        ❌ Плохой результат
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
    },

    // Вспомогательные методы для склонения слов
    getTaskWord(count) {
        if (count % 10 === 1 && count % 100 !== 11) return 'задача';
        if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'задачи';
        return 'задач';
    },

    getErrorWord(count) {
        if (count % 10 === 1 && count % 100 !== 11) return 'ошибка';
        if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'ошибки';
        return 'ошибок';
    },

    getStatusClass(jiraResult) {
        if (!jiraResult) return 'status-info';
        if (jiraResult.success && jiraResult.created_tasks?.length > 0) return 'status-success';
        if (jiraResult.errors?.length > 0) return 'status-error';
        return 'status-warning';
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
                UI.showMessage('Документ успешно обработан! Нажмите "Хороший результат" для создания задач в Jira', 'success');
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

    async createJiraTasks(resultId) {
        const resultCard = document.getElementById(resultId);
        const buttons = resultCard.querySelectorAll('.feedback-btn');
        const acceptBtn = resultCard.querySelector('.accept-btn');
        const jiraPlaceholder = document.getElementById(`jira-${resultId}`);

        // Получаем текст задач
        const summaryElement = resultCard.querySelector('.summary-content');
        const tasksText = summaryElement ? (summaryElement.textContent || summaryElement.innerText) : '';

        // Показываем загрузку
        acceptBtn.innerHTML = '⏳ Создаем задачи в Jira...';
        buttons.forEach(btn => btn.disabled = true);

        try {
            const requestData = {
                result_id: resultId,
                tasks_text: tasksText,
                project_key: 'LEARNJIRA',
                epic_key: ''
            };

            console.log('Создаем задачи в Jira:', requestData);

            const response = await fetch('/file/accept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            console.log('Ответ сервера:', result);

            if (response.ok && result.success && result.jira_result) {
                // Создаем HTML с результатами Jira
                const createdCount = result.jira_result.created_tasks?.length || 0;
                const errorsCount = result.jira_result.errors?.length || 0;

                let jiraHTML = '';
                let statusMessage = '';

                if (result.jira_result.success && createdCount > 0) {
                    jiraHTML = `
                        <div class="jira-success">
                            <h4>✅ Создано задач в Jira: ${createdCount}</h4>
                            <div class="jira-tasks-list">
                                ${result.jira_result.created_tasks.map((task, index) => `
                                    <div class="jira-task-item">
                                        <span class="task-number">${index + 1}.</span>
                                        <a href="${task.url}" target="_blank" class="jira-task-link">
                                            🎯 <strong>${task.key}</strong>: ${Utils.escapeHtml(task.title)}
                                        </a>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;

                    statusMessage = `Создано ${createdCount} ${UI.getTaskWord(createdCount)} в Jira`;
                } else if (createdCount === 0 && errorsCount > 0) {
                    jiraHTML = `
                        <div class="jira-error">
                            <h4>❌ Задачи не созданы (${errorsCount} ${UI.getErrorWord(errorsCount)})</h4>
                        </div>
                    `;
                    statusMessage = `Не удалось создать задачи в Jira`;
                }

                // Показываем ошибки если есть
                if (errorsCount > 0) {
                    jiraHTML += `
                        <div class="jira-warnings">
                            <h4>⚠️ Предупреждения (${errorsCount}):</h4>
                            <ul>
                                ${result.jira_result.errors.map((error, index) => 
                                    `<li><strong>${index + 1}.</strong> ${Utils.escapeHtml(error)}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    `;
                }

                // Добавляем статусный бейдж
                jiraHTML += `
                    <div class="result-summary">
                        <div class="status-badge ${UI.getStatusClass(result.jira_result)}">
                            ${statusMessage}
                        </div>
                    </div>
                `;

                // Отображаем результаты
                jiraPlaceholder.innerHTML = jiraHTML;
                jiraPlaceholder.style.display = 'block';

                // Обновляем кнопки
                acceptBtn.innerHTML = '✅ Задачи созданы в Jira';
                acceptBtn.style.opacity = '0.7';

                // Добавляем визуальный статус
                resultCard.classList.add('feedback-positive');

                UI.showMessage(result.message || `Создано ${createdCount} ${UI.getTaskWord(createdCount)} в Jira!`, 'success');

            } else {
                throw new Error(Utils.getErrorMessage(result) || 'Ошибка создания задач в Jira');
            }
        } catch (error) {
            console.error('Jira creation error:', error);

            // Показываем ошибку в placeholder
            jiraPlaceholder.innerHTML = `
                <div class="jira-error">
                    <h4>❌ Ошибка создания задач</h4>
                    <p>${Utils.getErrorMessage(error)}</p>
                </div>
            `;
            jiraPlaceholder.style.display = 'block';

            // Возвращаем кнопку в исходное состояние
            acceptBtn.innerHTML = '✅ Хороший результат - создать задачи в Jira';
            buttons.forEach(btn => btn.disabled = false);

            UI.showMessage(`Ошибка создания задач: ${Utils.getErrorMessage(error)}`, 'error');
        }
    },

    async giveFeedback(resultId, feedbackType) {
        const resultCard = document.getElementById(resultId);
        const buttons = resultCard.querySelectorAll('.feedback-btn');
        const targetButton = resultCard.querySelector(`.${feedbackType}-btn`);

        // Показываем загрузку
        targetButton.innerHTML = '⏳ Отправка...';
        buttons.forEach(btn => btn.disabled = true);

        try {
            // Получаем текст задач для отправки
            const summaryElement = resultCard.querySelector('.summary-content');
            const tasksText = summaryElement ? (summaryElement.textContent || summaryElement.innerText) : '';

            const requestData = {
                result_id: resultId,
                tasks_text: tasksText,
                feedback_type: feedbackType,
                reason: 'Результат отклонен пользователем',
                timestamp: new Date().toISOString()
            };

            console.log('Отправляем обратную связь:', requestData);

            const response = await fetch('/file/reject', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            console.log('Ответ сервера:', result);

            if (response.ok && result.success) {
                targetButton.innerHTML = '❌ Учтено';
                targetButton.style.opacity = '0.7';

                // Добавляем визуальный статус
                resultCard.classList.add('feedback-negative');

                UI.showMessage(result.message || 'Обратная связь учтена!', 'success');
            } else {
                throw new Error(Utils.getErrorMessage(result) || 'Ошибка отправки обратной связи');
            }
        } catch (error) {
            console.error('Feedback error:', error);

            // Возвращаем кнопку в исходное состояние
            targetButton.innerHTML = '👎 Плохой результат';
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