/**
 * Модуль для управления обратной связью по результатам обработки документов
 * Включает функции для создания задач в Jira и отклонения результатов
 */

const FeedbackManager = {
    // Конфигурация
    config: {
        endpoints: {
            accept: '/file/accept/',
            reject: '/file/reject/'
        },
        timeouts: {
            request: 30000, // 30 секунд
            message: 5000   // 5 секунд
        }
    },

    /**
     * Создание задач в Jira на основе обработанного документа
     * @param {string} resultId - ID результата обработки
     * @param {Object} options - Дополнительные параметры
     */
    async createJiraTasks(resultId, options = {}) {
        console.log('=== СОЗДАНИЕ ЗАДАЧ В JIRA ===');
        console.log('Result ID:', resultId);
        console.log('Options:', options);

        const resultCard = document.getElementById(resultId);
        if (!resultCard) {
            console.error('Result card not found:', resultId);
            this.showError('Карточка результата не найдена');
            return;
        }

        const elements = this.getCardElements(resultCard);
        if (!elements) return;

        // Извлекаем данные для создания задач
        const requestData = this.prepareJiraRequestData(resultId, resultCard, options);

        // Устанавливаем состояние загрузки
        this.setLoadingState(elements, 'Создаем задачи в Jira...');

        try {
            const response = await this.makeRequest(this.config.endpoints.accept, requestData);
            console.log('Jira response:', response);

            if (this.isSuccessResponse(response)) {
                await this.handleJiraSuccess(resultCard, response);
            } else {
                throw new Error(this.extractErrorMessage(response));
            }

        } catch (error) {
            console.error('Jira creation error:', error);
            this.handleJiraError(resultCard, error);
        }
    },

    /**
     * Отклонение результата обработки
     * @param {string} resultId - ID результата обработки
     * @param {string} reason - Причина отклонения
     */
    async rejectResult(resultId, reason = 'Результат отклонен пользователем') {
        console.log('=== ОТКЛОНЕНИЕ РЕЗУЛЬТАТА ===');
        console.log('Result ID:', resultId);
        console.log('Reason:', reason);

        const resultCard = document.getElementById(resultId);
        if (!resultCard) {
            console.error('Result card not found:', resultId);
            this.showError('Карточка результата не найдена');
            return;
        }

        const elements = this.getCardElements(resultCard);
        if (!elements) return;

        // Подготавливаем данные для отклонения
        const requestData = this.prepareRejectRequestData(resultId, resultCard, reason);

        // Устанавливаем состояние загрузки
        this.setRejectLoadingState(elements);

        try {
            const response = await this.makeRequest(this.config.endpoints.reject, requestData);
            console.log('Reject response:', response);

            if (this.isSuccessResponse(response)) {
                this.handleRejectSuccess(resultCard, elements);
            } else {
                throw new Error(this.extractErrorMessage(response));
            }

        } catch (error) {
            console.error('Reject error:', error);
            this.handleRejectError(elements, error);
        }
    },

    /**
     * Получение элементов карточки результата
     */
    getCardElements(resultCard) {
        const elements = {
            acceptBtn: resultCard.querySelector('.accept-btn'),
            rejectBtn: resultCard.querySelector('.reject-btn'),
            allBtns: resultCard.querySelectorAll('.feedback-btn'),
            summaryContent: resultCard.querySelector('.summary-content'),
            jiraPlaceholder: resultCard.querySelector(`[id^="jira-"]`),
            statusIndicator: resultCard.querySelector(`[id^="status-"]`)
        };

        if (!elements.acceptBtn || !elements.rejectBtn) {
            console.error('Required buttons not found in result card');
            this.showError('Кнопки обратной связи не найдены');
            return null;
        }

        return elements;
    },

    /**
     * Подготовка данных для создания задач в Jira
     */
    prepareJiraRequestData(resultId, resultCard, options) {
        const summaryElement = resultCard.querySelector('.summary-content');
        const tasksText = summaryElement ?
            (summaryElement.textContent || summaryElement.innerText) : '';

        return {
            result_id: resultId,
            tasks_text: tasksText.trim(),
            project_key: options.projectKey || 'MEET2JIRA',
            epic_key: options.epicKey || '',
            assignee: options.assignee || null,
            priority: options.priority || 'Medium',
            ...options.customFields
        };
    },

    /**
     * Подготовка данных для отклонения результата
     */
    prepareRejectRequestData(resultId, resultCard, reason) {
        const summaryElement = resultCard.querySelector('.summary-content');
        const tasksText = summaryElement ?
            (summaryElement.textContent || summaryElement.innerText) : '';

        return {
            result_id: resultId,
            tasks_text: tasksText.trim(),
            feedback_type: 'reject',
            reason: reason,
            timestamp: new Date().toISOString()
        };
    },

    /**
     * Выполнение HTTP запроса
     */
    async makeRequest(url, data) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeouts.request);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await this.extractResponseError(response);
                throw new Error(errorText);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('Превышено время ожидания запроса');
            }
            throw error;
        }
    },

    /**
     * Извлечение ошибки из ответа сервера
     */
    async extractResponseError(response) {
        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                return this.extractErrorMessage(errorData);
            } else {
                return await response.text() || `HTTP ${response.status}: ${response.statusText}`;
            }
        } catch {
            return `HTTP ${response.status}: ${response.statusText}`;
        }
    },

    /**
     * Проверка успешности ответа
     */
    isSuccessResponse(response) {
        return response &&
               response.status === "success" &&
               !response.error;
    },

    /**
     * Извлечение сообщения об ошибке
     */
    extractErrorMessage(error) {
        if (typeof error === 'string') return error;
        if (error?.message) return error.message;
        if (error?.error_message) return error.error_message;
        if (error?.error) return error.error;
        if (error?.detail) {
            if (typeof error.detail === 'string') return error.detail;
            if (Array.isArray(error.detail)) {
                return error.detail.map(err => {
                    const field = err.loc ? err.loc.join('.') : 'field';
                    const message = err.msg || err.message || 'validation error';
                    return `${field}: ${message}`;
                }).join('; ');
            }
            return JSON.stringify(error.detail);
        }
        return 'Неизвестная ошибка';
    },

    /**
     * Установка состояния загрузки для создания задач
     */
    setLoadingState(elements, message) {
        elements.acceptBtn.innerHTML = `⏳ ${message}`;
        elements.allBtns.forEach(btn => btn.disabled = true);
    },

    /**
     * Установка состояния загрузки для отклонения
     */
    setRejectLoadingState(elements) {
        elements.rejectBtn.innerHTML = '⏳ Отправка...';
        elements.allBtns.forEach(btn => btn.disabled = true);
    },

    /**
     * Обработка успешного создания задач в Jira
     */
    async handleJiraSuccess(resultCard, response) {
        const jiraData = response.jira_result || response.task_result || response.data || response;
        const elements = this.getCardElements(resultCard);

        console.log('Jira success data:', jiraData);

        const createdCount = jiraData.created_tasks?.length || jiraData.tasks?.length || 0;
        const errorsCount = jiraData.errors?.length || 0;

        if (jiraData.success === true || createdCount > 0) {
            this.renderJiraSuccess(elements.jiraPlaceholder, jiraData, createdCount);
            this.setSuccessState(elements, createdCount);
            this.showSuccess(`Создано ${createdCount} ${this.getTaskWord(createdCount)} в Jira`);
        } else if (errorsCount > 0) {
            this.renderJiraErrors(elements.jiraPlaceholder, jiraData.errors);
            this.showError('Ошибки при создании задач в Jira');
        } else {
            this.renderJiraDebugInfo(elements.jiraPlaceholder, response);
            this.showWarning('Получен неожиданный ответ от сервера');
        }

        // Добавляем визуальную метку
        resultCard.classList.add('feedback-positive');
    },

    /**
     * Отображение успешно созданных задач
     */
    renderJiraSuccess(placeholder, jiraData, createdCount) {
        const tasks = jiraData.created_tasks || jiraData.tasks || [];

        const jiraHTML = `
            <div class="jira-success">
                <h4>✅ Создано задач в Jira: ${createdCount}</h4>
                <div class="jira-tasks-list">
                    ${tasks.map((task, index) => `
                        <div class="jira-task-item">
                            <span class="task-number">${index + 1}.</span>
                            <a href="${task.url || '#'}" target="_blank" class="jira-task-link">
                                🎯 <strong>${task.key || 'TASK-' + (index + 1)}</strong>: ${this.escapeHtml(task.title || task.summary || 'Задача создана')}
                            </a>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        placeholder.innerHTML = jiraHTML;
        placeholder.style.display = 'block';
    },

    /**
     * Отображение ошибок создания задач
     */
    renderJiraErrors(placeholder, errors) {
        const jiraHTML = `
            <div class="jira-error">
                <h4>❌ Ошибки при создании задач (${errors.length})</h4>
                <ul class="error-list">
                    ${errors.map((error, index) =>
                        `<li><strong>${index + 1}.</strong> ${this.escapeHtml(String(error))}</li>`
                    ).join('')}
                </ul>
            </div>
        `;

        placeholder.innerHTML = jiraHTML;
        placeholder.style.display = 'block';
    },

    /**
     * Отображение отладочной информации
     */
    renderJiraDebugInfo(placeholder, response) {
        const jiraHTML = `
            <div class="jira-info">
                <h4>ℹ️ Ответ от сервера</h4>
                <details>
                    <summary>Показать детали</summary>
                    <pre class="debug-info">${JSON.stringify(response, null, 2)}</pre>
                </details>
            </div>
        `;

        placeholder.innerHTML = jiraHTML;
        placeholder.style.display = 'block';
    },

    /**
     * Установка состояния успеха
     */
    setSuccessState(elements, createdCount) {
        elements.acceptBtn.innerHTML = '✅ Обработано';
        elements.acceptBtn.style.opacity = '0.7';
        elements.acceptBtn.disabled = true;
    },

    /**
     * Обработка ошибки создания задач
     */
    handleJiraError(resultCard, error) {
        const elements = this.getCardElements(resultCard);
        const errorMessage = this.extractErrorMessage(error);

        // Показываем ошибку в placeholder
        elements.jiraPlaceholder.innerHTML = `
            <div class="jira-error">
                <h4>❌ Ошибка создания задач</h4>
                <p class="error-message">${this.escapeHtml(errorMessage)}</p>
                <button onclick="FeedbackManager.retryJiraCreation('${resultCard.id}')" class="retry-btn">
                    🔄 Попробовать снова
                </button>
            </div>
        `;
        elements.jiraPlaceholder.style.display = 'block';

        // Возвращаем кнопки в исходное состояние
        elements.acceptBtn.innerHTML = '✅ Хороший результат - создать задачи в Jira';
        elements.allBtns.forEach(btn => btn.disabled = false);

        this.showError(`Ошибка создания задач: ${errorMessage}`);
    },

    /**
     * Обработка успешного отклонения
     */
    handleRejectSuccess(resultCard, elements) {
        elements.rejectBtn.innerHTML = '❌ Учтено';
        elements.rejectBtn.style.opacity = '0.7';
        elements.rejectBtn.disabled = true;

        // Добавляем визуальную метку
        resultCard.classList.add('feedback-negative');

        this.showSuccess('Обратная связь учтена!');
    },

    /**
     * Обработка ошибки отклонения
     */
    handleRejectError(elements, error) {
        const errorMessage = this.extractErrorMessage(error);

        // Возвращаем кнопку в исходное состояние
        elements.rejectBtn.innerHTML = '❌ Плохой результат';
        elements.allBtns.forEach(btn => btn.disabled = false);

        this.showError(`Ошибка обратной связи: ${errorMessage}`);
    },

    /**
     * Повторная попытка создания задач
     */
    async retryJiraCreation(resultId) {
        await this.createJiraTasks(resultId);
    },

    /**
     * Утилитарные функции
     */
    getTaskWord(count) {
        if (count % 10 === 1 && count % 100 !== 11) return 'задача';
        if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'задачи';
        return 'задач';
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    showSuccess(message) {
        this.showMessage(message, 'success');
    },

    showError(message) {
        this.showMessage(message, 'error');
    },

    showWarning(message) {
        this.showMessage(message, 'warning');
    },

    showMessage(text, type) {
        const messageElement = document.getElementById('message');
        if (messageElement) {
            // Создаем новый элемент сообщения
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = this.escapeHtml(text);

            // Очищаем предыдущие сообщения того же типа
            const existingMessages = messageElement.querySelectorAll(`.message.${type}`);
            existingMessages.forEach(msg => msg.remove());

            // Добавляем новое сообщение
            messageElement.appendChild(messageDiv);

            // Автоудаление сообщения
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, this.config.timeouts.message);
        } else {
            console.log(`${type.toUpperCase()}: ${text}`);
        }
    }
};

// Экспорт для глобального доступа
if (typeof window !== 'undefined') {
    window.FeedbackManager = FeedbackManager;
}

// Экспорт для модульных систем
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackManager;
}
