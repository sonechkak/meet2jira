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
        console.log('=== ПОКАЗ РЕЗУЛЬТАТА ===');
        console.log('Full result:', result);

        const fileIcon = Utils.getFileIcon(result.document_name || 'unknown');
        const summaryContent = Utils.extractSummary(result.summary);

        const resultId = `result-${Date.now()}`;
        const summaryId = `summary-${Date.now()}`;

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

    async createJiraTasks(resultId) {
        const resultCard = document.getElementById(resultId);
        if (!resultCard) {
            console.error('Result card not found:', resultId);
            return;
        }

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
            // Минимальный объект запроса
            const requestData = {
                result_id: resultId,
                tasks_text: tasksText,
                project_key: 'LEARNJIRA',
                epic_key: ''
            };

            console.log('Создаем задачи в Jira:', requestData);

            const response = await fetch('/file/accept', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            console.log('=== JIRA RESPONSE DEBUG ===');
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);

            if (!response.ok) {
                let errorText;
                try {
                    const errorData = await response.json();
                    errorText = Utils.getErrorMessage(errorData);
                } catch {
                    errorText = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorText);
            }

            const result = await response.json();
            console.log('Full response:', result);

            const isSuccess = result.status === "success" && !result.error;

            if (isSuccess) {
                // Ищем jira_result в разных местах
                const jiraData = result.jira_result || result.task_result || result.data || result;

                console.log('Jira data:', jiraData);

                const createdCount = jiraData.created_tasks?.length ||
                                   jiraData.tasks?.length || 0;
                const errorsCount = jiraData.errors?.length || 0;

                let jiraHTML = '';
                let statusMessage = '';

                // Проверяем успешность создания задач
                const isJiraSuccess = jiraData.success === true ||
                                    jiraData.status === "success" ||
                                    createdCount > 0;

                if (isJiraSuccess && createdCount > 0) {
                    const tasks = jiraData.created_tasks || jiraData.tasks || [];

                    jiraHTML = `
                        <div class="jira-success">
                            <h4>✅ Создано задач в Jira: ${createdCount}</h4>
                            <div class="jira-tasks-list">
                                ${tasks.map((task, index) => `
                                    <div class="jira-task-item">
                                        <span class="task-number">${index + 1}.</span>
                                        <a href="${task.url || '#'}" target="_blank" class="jira-task-link">
                                            🎯 <strong>${task.key || 'TASK-' + (index + 1)}</strong>: ${Utils.escapeHtml(task.title || task.summary || 'Задача создана')}
                                        </a>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                    statusMessage = `Создано ${createdCount} ${UI.getTaskWord(createdCount)} в Jira`;
                } else if (errorsCount > 0) {
                    jiraHTML = `
                        <div class="jira-error">
                            <h4>❌ Ошибки при создании задач (${errorsCount})</h4>
                        </div>
                    `;
                    statusMessage = `Ошибки при создании задач`;
                } else {
                    // Показываем что получили для отладки
                    jiraHTML = `
                        <div class="jira-info">
                            <h4>ℹ️ Ответ от сервера</h4>
                            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 12px; max-height: 200px; overflow-y: auto;">${JSON.stringify(result, null, 2)}</pre>
                        </div>
                    `;
                    statusMessage = 'Получен ответ от сервера';
                }

                // Показываем ошибки если есть
                if (errorsCount > 0 && jiraData.errors) {
                    jiraHTML += `
                        <div class="jira-warnings">
                            <h4>⚠️ Ошибки (${errorsCount}):</h4>
                            <ul>
                                ${jiraData.errors.map((error, index) =>
                        `<li><strong>${index + 1}.</strong> ${Utils.escapeHtml(String(error))}</li>`
                    ).join('')}
                            </ul>
                        </div>
                    `;
                }

                // Отображаем результаты
                jiraPlaceholder.innerHTML = jiraHTML;
                jiraPlaceholder.style.display = 'block';

                // Обновляем кнопки
                acceptBtn.innerHTML = '✅ Обработано';
                acceptBtn.style.opacity = '0.7';

                // Добавляем визуальный статус
                resultCard.classList.add('feedback-positive');

                UI.showMessage(statusMessage, 'success');

            } else {
                // Обработка ошибки
                const errorMsg = result.error_message || Utils.getErrorMessage(result) || 'Ошибка создания задач в Jira';
                throw new Error(errorMsg);
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
        if (!resultCard) {
            console.error('Result card not found:', resultId);
            return;
        }

        const buttons = resultCard.querySelectorAll('.feedback-btn');
        const targetButton = resultCard.querySelector(`.${feedbackType}-btn`);

        // Показываем загрузку
        targetButton.innerHTML = '⏳ Отправка...';
        buttons.forEach(btn => btn.disabled = true);

        try {
            // Получаем текст задач для отправки
            const summaryElement = resultCard.querySelector('.summary-content');
            const tasksText = summaryElement ? (summaryElement.textContent || summaryElement.innerText) : '';

            // Минимальный объект запроса
            const requestData = {
                result_id: resultId,
                tasks_text: tasksText,
                feedback_type: feedbackType,
                reason: 'Результат отклонен пользователем',
            };

            console.log('Отправляем обратную связь:', requestData);

            const response = await fetch('/file/reject', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                let errorText;
                try {
                    const errorData = await response.json();
                    errorText = Utils.getErrorMessage(errorData);
                } catch {
                    errorText = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorText);
            }

            const result = await response.json();
            console.log('Ответ сервера на reject:', result);

            const isSuccess = result.status === "success" && !result.error;

            if (isSuccess) {
                targetButton.innerHTML = '❌ Учтено';
                targetButton.style.opacity = '0.7';

                // Добавляем визуальный статус
                resultCard.classList.add('feedback-negative');

                UI.showMessage('Обратная связь учтена!', 'success');
            } else {
                const errorMsg = result.error_message || Utils.getErrorMessage(result) || 'Ошибка отправки обратной связи';
                throw new Error(errorMsg);
            }
        } catch (error) {
            console.error('Feedback error:', error);

            // Возвращаем кнопку в исходное состояние
            targetButton.innerHTML = '❌ Плохой результат';
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

// Запуск приложения
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== DOM LOADED ===');
    initializeEventListeners();
});

// Экспортируем Actions для глобального доступа
window.Actions = Actions;