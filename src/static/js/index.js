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
        console.log('=== GETTING ERROR MESSAGE ===');
        console.log('Error type:', typeof error);
        console.log('Error:', error);

        if (typeof error === 'string') {
            console.log('String error:', error);
            return error;
        }

        if (error?.message) {
            console.log('Error.message:', error.message);
            return error.message;
        }

        if (error?.detail) {
            console.log('Error.detail:', error.detail);
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

        if (error?.error) {
            console.log('Error.error:', error.error);
            return error.error;
        }

        if (error?.error_message) {
            console.log('Error.error_message:', error.error_message);
            return error.error_message;
        }

        console.log('Fallback to unknown error');
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
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    isValidFile(file) {
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        const isValidType = CONFIG.allowedTypes.includes(file.type);
        const isValidExtension = CONFIG.allowedExtensions.includes(fileExtension);

        console.log('File validation:', {
            fileName: file.name,
            fileType: file.type,
            fileExtension: fileExtension,
            isValidType: isValidType,
            isValidExtension: isValidExtension
        });

        return isValidType || isValidExtension;
    },

    formatContent(content) {
        if (!content) return '';
        if (Array.isArray(content)) return content.join('\n');
        if (typeof content === 'object' && content !== null) return JSON.stringify(content, null, 2);
        return String(content);
    },

    // Извлечение summary с учетом различных схем ответа
    extractSummary(summaryData) {
        console.log('=== ИЗВЛЕЧЕНИЕ SUMMARY ===');
        console.log('Summary data:', summaryData);
        console.log('Summary type:', typeof summaryData);

        if (!summaryData) {
            console.log('Summary is null/undefined');
            return 'Нет данных для отображения';
        }

        // Если это строка
        if (typeof summaryData === 'string') {
            console.log('Summary is string:', summaryData);
            return summaryData;
        }

        // Если это объект
        if (typeof summaryData === 'object') {
            console.log('Summary is object, keys:', Object.keys(summaryData));

            // Список возможных полей где может быть контент
            const possibleFields = [
                'summary',           // SummaryResponseSchema.summary
                'content',           // общее поле content
                'text',              // общее поле text
                'tasks',             // поле tasks
                'response_text',     // LLMServiceResponseSchema.response_text
                'response_data',     // LLMServiceResponseSchema.response_data
                'data',              // общее поле data
                'result',            // общее поле result
                'value'              // общее поле value
            ];

            // Ищем непустое значение в порядке приоритета
            for (const field of possibleFields) {
                const value = summaryData[field];
                if (value && value !== '' && value !== '{}' && JSON.stringify(value) !== '{}') {
                    console.log(`Found content in field '${field}':`, value);

                    // Если найденное значение тоже объект, попробуем извлечь из него
                    if (typeof value === 'object') {
                        return this.formatContent(value);
                    }
                    return String(value);
                }
            }

            // Если ничего конкретного не найдено, форматируем весь объект
            console.log('No specific field found, formatting entire object');
            return this.formatContent(summaryData);
        }

        // Для других типов
        console.log('Summary is other type, converting to string');
        return String(summaryData);
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
        // Создаем новый элемент сообщения
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = Utils.escapeHtml(text);

        // Очищаем предыдущие сообщения этого типа
        const existingMessages = message.querySelectorAll(`.message.${type}`);
        existingMessages.forEach(msg => msg.remove());

        // Добавляем новое сообщение
        message.appendChild(messageDiv);

        // Автоудаление сообщения
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, type === 'error' ? 10000 : 5000); // Ошибки показываем дольше
    },

    clearMessage() {
        if (message) {
            message.innerHTML = '';
        }
    },

    showResult(result) {
        console.log('=== ПОКАЗ РЕЗУЛЬТАТА ===');
        console.log('Full result:', result);

        const fileIcon = Utils.getFileIcon(result.document_name || 'unknown');
        const summaryContent = Utils.extractSummary(result.summary);

        const resultId = `result-${Date.now()}`;
        const summaryId = `summary-${Date.now()}`;

        console.log('Generated IDs:', { resultId, summaryId });
        console.log('Summary content:', summaryContent);

        const resultHTML = `
            <div class="result-card" id="${resultId}">
                <div class="result-header">
                    <div class="document-name">${fileIcon} ${Utils.escapeHtml(result.document_name || 'Документ')}</div>
                    <div class="model-badge">🤖 ${result.model || 'AI Model'}</div>
                </div>

                <div class="summary-label">Найденные задачи:</div>
                <div class="summary-content" id="${summaryId}">
                    ${Utils.escapeHtml(summaryContent).replace(/\n/g, '<br>')}
                </div>

                <div class="jira-placeholder" id="jira-${resultId}" style="display: none;">
                    <!-- Результаты Jira появятся здесь после нажатия "Хороший результат" -->
                </div>

                <div class="action-buttons">
                    <button class="copy-btn" onclick="Actions.copySummary('${summaryId}')">
                        📋 Копировать задачи
                    </button>
                    <button class="feedback-btn accept-btn" onclick="Actions.createJiraTasks('${resultId}')">
                        ✅ Хороший результат - создать задачи в Jira
                    </button>
                    <button class="feedback-btn reject-btn" onclick="Actions.rejectResult('${resultId}')">
                        ❌ Плохой результат
                    </button>
                </div>

                <div class="status-indicator" id="status-${resultId}" style="display: none;"></div>
            </div>
        `;

        console.log('Inserting result HTML...');
        resultsList.innerHTML = resultHTML + resultsList.innerHTML;
        resultsSection.style.display = 'block';

        console.log('Result displayed successfully');

        setTimeout(() => {
            resultsSection.scrollIntoView({behavior: 'smooth', block: 'start'});
        }, 100);
    }
};

// Основные действия
const Actions = {
    async processFile() {
        const file = fileInput.files[0];
        if (!file) {
            console.log('No file selected');
            return;
        }

        console.log('=== НАЧАЛО ОБРАБОТКИ ФАЙЛА ===');
        console.log('Файл:', file.name, file.type, file.size);

        if (!Utils.isValidFile(file)) {
            UI.showMessage('Неподдерживаемый формат файла. Используйте PDF, DOCX, TXT, MD или изображения (JPG, PNG, TIFF, BMP).', 'error');
            return;
        }

        UI.setProcessingState(true);
        UI.clearMessage();

        // Создаем минимальный FormData с только файлом
        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('Отправка запроса на сервер...');

            const response = await fetch('/file/process', {
                method: 'POST',
                body: formData,
                // НЕ добавляем Content-Type header - браузер установит его автоматически с boundary
            });

            console.log('=== ОТВЕТ СЕРВЕРА ===');
            console.log('Status:', response.status);
            console.log('OK:', response.ok);
            console.log('Headers:', Object.fromEntries(response.headers.entries()));

            // Проверяем Content-Type ответа
            const contentType = response.headers.get('content-type');
            console.log('Response Content-Type:', contentType);

            if (!response.ok) {
                // Если ответ не успешный, пытаемся получить текст ошибки
                let errorText;
                try {
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorText = Utils.getErrorMessage(errorData);
                    } else {
                        errorText = await response.text();
                    }
                } catch (parseError) {
                    console.error('Error parsing error response:', parseError);
                    errorText = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorText);
            }

            // Получаем и парсим успешный ответ
            let result;
            try {
                if (contentType && contentType.includes('application/json')) {
                    result = await response.json();
                } else {
                    const responseText = await response.text();
                    console.log('Raw response text:', responseText);
                    try {
                        result = JSON.parse(responseText);
                    } catch (jsonError) {
                        console.error('Failed to parse JSON:', jsonError);
                        throw new Error(`Invalid JSON response: ${responseText.substring(0, 200)}...`);
                    }
                }
            } catch (parseError) {
                console.error('Error parsing response:', parseError);
                throw new Error('Не удалось обработать ответ сервера');
            }

            console.log('=== PARSED RESPONSE ===');
            console.log('Full result:', result);
            console.log('Result keys:', Object.keys(result));

            // Улучшенная проверка успешности ответа
            const isSuccess = result.status === "success" && !result.error;
            const hasValidSummary = result.summary !== undefined && result.summary !== null;

            console.log('Success check:', {
                status: result.status,
                error: result.error,
                isSuccess: isSuccess,
                hasValidSummary: hasValidSummary
            });

            if (isSuccess && hasValidSummary) {
                console.log('✅ SUCCESS - показываем результат');
                UI.showResult(result);
                UI.showMessage('Документ успешно обработан!', 'success');
            } else {
                console.log('❌ FAILURE - условие не выполнено');
                console.log('Result status:', result.status);
                console.log('Result error:', result.error);
                console.log('Result error_message:', result.error_message);

                const errorMsg = result.error_message ||
                                result.error ||
                                Utils.getErrorMessage(result) ||
                                'Ошибка обработки файла';
                throw new Error(errorMsg);
            }

        } catch (error) {
            console.error('=== ОШИБКА В CATCH ===');
            console.error('Error:', error);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);

            const errorMessage = Utils.getErrorMessage(error);
            UI.showMessage(`Ошибка: ${errorMessage}`, 'error');
        } finally {
            console.log('=== ЗАВЕРШЕНИЕ ОБРАБОТКИ ===');
            UI.setProcessingState(false);
            fileInput.value = '';
        }
    },

    copySummary(elementId) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.error('Element not found:', elementId);
            return;
        }

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

    // Переадресация на FeedbackManager для создания задач
    async createJiraTasks(resultId, options = {}) {
        if (typeof window.FeedbackManager !== 'undefined') {
            await window.FeedbackManager.createJiraTasks(resultId, options);
        } else {
            console.error('FeedbackManager not available');
            UI.showMessage('Модуль обратной связи не загружен', 'error');
        }
    },

    // Переадресация на FeedbackManager для отклонения результата
    async rejectResult(resultId, reason = 'Результат отклонен пользователем') {
        if (typeof window.FeedbackManager !== 'undefined') {
            await window.FeedbackManager.rejectResult(resultId, reason);
        } else {
            console.error('FeedbackManager not available');
            UI.showMessage('Модуль обратной связи не загружен', 'error');
        }
    },

    // Обратная совместимость для старых вызовов
    async giveFeedback(resultId, feedbackType) {
        if (feedbackType === 'reject') {
            await this.rejectResult(resultId);
        } else {
            console.warn('Unknown feedback type:', feedbackType);
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
    // Проверяем что все элементы существуют
    if (!fileInput) {
        console.error('fileInput element not found');
        return;
    }
    if (!uploadArea) {
        console.error('uploadArea element not found');
        return;
    }

    fileInput.addEventListener('change', Actions.processFile);
    uploadArea.addEventListener('dragover', DragDrop.handleDragOver);
    uploadArea.addEventListener('dragleave', DragDrop.handleDragLeave);
    uploadArea.addEventListener('drop', DragDrop.handleDrop);

    console.log('Event listeners initialized');
}

// Проверка загрузки зависимостей
function checkDependencies() {
    if (typeof window.FeedbackManager === 'undefined') {
        console.warn('FeedbackManager not loaded. Feedback functionality may be limited.');

        // Показываем предупреждение пользователю
        setTimeout(() => {
            UI.showMessage('Модуль обратной связи не загружен. Некоторые функции могут быть недоступны.', 'warning');
        }, 1000);
    } else {
        console.log('All dependencies loaded successfully');
    }
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== DOM LOADED ===');
    initializeEventListeners();

    setTimeout(checkDependencies, 100);
});

// Экспортируем Actions
window.Actions = Actions;
