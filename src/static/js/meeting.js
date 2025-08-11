// Данные встреч из базы данных
let meetingsData = [];

// Функция для загрузки встреч из API
async function loadMeetingsFromAPI() {
    try {
        const response = await fetch('/meetings');
        if (response.ok) {
            meetingsData = await response.json();
            displayMeetingsList();
        } else {
            console.error('Ошибка загрузки встреч:', response.statusText);
            showMeetingsError('Не удалось загрузить список встреч');
        }
    } catch (error) {
        console.error('Ошибка соединения:', error);
        showMeetingsError('Ошибка соединения с сервером');
    }
}

// Функция для отображения ошибок в секции встреч
function showMeetingsError(message) {
    const meetingsList = document.getElementById('meetingsList');
    if (meetingsList) {
        meetingsList.innerHTML = `<div class="empty-meetings" style="color: #d32f2f;">${message}</div>`;
    } else {
        console.error('Элемент meetingsList не найден');
    }
}

// Функция для отображения встреч
function displayMeetingsList() {
    const meetingsList = document.getElementById('meetingsList');

    if (!meetingsList) {
        console.error('Элемент meetingsList не найден');
        return;
    }

    if (meetingsData.length === 0) {
        meetingsList.innerHTML = '<div class="empty-meetings">Встречи не найдены</div>';
        return;
    }

    meetingsList.innerHTML = meetingsData.map(meeting => {
        // Определяем статус встречи на основе поля status
        let statusClass = '';
        let statusText = '';

        switch(meeting.status) {
            case 'completed':
                statusClass = 'status-processed';
                statusText = 'Завершено';
                break;
            case 'processing':
                statusClass = 'status-pending';
                statusText = 'Обрабатывается';
                break;
            case 'scheduled':
                statusClass = 'status-pending';
                statusText = 'Запланировано';
                break;
            case 'failed':
                statusClass = 'status-failed';
                statusText = 'Ошибка';
                break;
            default:
                statusClass = 'status-pending';
                statusText = 'Неизвестно';
        }

        // Форматируем дату встречи
        const meetingDate = new Date(meeting.meeting_date).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Форматируем дату создания
        const createdDate = new Date(meeting.created_at).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Участники или описание
        const participants = meeting.participants || 'Участники не указаны';
        const duration = meeting.duration_minutes ? `⏱️ ${meeting.duration_minutes} мин` : '';

        return `
            <div class="meeting-item" onclick="selectMeetingItem(${meeting.id})">
                <div class="meeting-title">${meeting.title}</div>
                <div class="meeting-date">📅 ${meetingDate}</div>
                ${participants ? `<div class="meeting-participants">👥 ${participants}</div>` : ''}
                ${duration ? `<div class="meeting-duration">${duration}</div>` : ''}
                ${meeting.file_name ? `<div class="meeting-file">📄 ${meeting.file_name}</div>` : ''}
                <div class="meeting-created">📝 Создано: ${createdDate}</div>
                <span class="meeting-status ${statusClass}">${statusText}</span>
                ${meeting.description ? `<div class="meeting-description">${meeting.description}</div>` : ''}
            </div>
        `;
    }).join('');
}

// Функция для выбора встречи
function selectMeetingItem(meetingId) {
    const meeting = meetingsData.find(m => m.id === meetingId);
    if (meeting) {
        console.log('Выбрана встреча:', meeting);
        showMeetingResults(meeting);
    }
}

// Функция для отображения результатов встречи
async function showMeetingResults(meeting) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('resultsList');

    if (!resultsSection || !resultsList) {
        console.error('Элементы результатов не найдены');
        return;
    }

    if (meeting.status === 'completed') {
        try {
            // Загружаем задачи для конкретной встречи
            const response = await fetch(`/meetings/${meeting.id}/tasks`);
            if (response.ok) {
                const tasks = await response.json();

                if (tasks.length > 0) {
                    resultsList.innerHTML = tasks.map(task => `
                        <div class="result-item">
                            <h3>${task.title || task.summary}</h3>
                            <p><strong>Описание:</strong> ${task.description || 'Описание отсутствует'}</p>
                            <p><strong>Приоритет:</strong> ${task.priority || 'Medium'}</p>
                            <p><strong>Исполнитель:</strong> ${task.assignee || 'Не назначен'}</p>
                            <p><strong>Статус:</strong> ${task.status || 'To Do'}</p>
                            ${task.jira_key ? `<p><strong>Jira:</strong> <a href="${task.jira_url || '#'}" target="_blank">${task.jira_key}</a></p>` : ''}
                            <p><small>Создано: ${new Date(task.created_at).toLocaleDateString('ru-RU')}</small></p>
                        </div>
                    `).join('');
                } else {
                    resultsList.innerHTML = '<div class="result-item">Задачи для этой встречи не найдены</div>';
                }
            } else {
                resultsList.innerHTML = '<div class="result-item">Ошибка загрузки задач</div>';
            }
        } catch (error) {
            console.error('Ошибка загрузки задач:', error);
            resultsList.innerHTML = '<div class="result-item">Ошибка соединения при загрузке задач</div>';
        }

        resultsSection.style.display = 'block';
    } else if (meeting.status === 'failed') {
        resultsList.innerHTML = `<div class="result-item">Произошла ошибка при обработке встречи</div>`;
        resultsSection.style.display = 'block';
    } else if (meeting.status === 'processing') {
        resultsList.innerHTML = '<div class="result-item">Встреча обрабатывается, пожалуйста подождите...</div>';
        resultsSection.style.display = 'block';
    } else {
        resultsList.innerHTML = '<div class="result-item">Встреча запланирована, но еще не обработана</div>';
        resultsSection.style.display = 'block';
    }
}

// Функция для ручного обновления списка встреч
function refreshMeetings() {
    loadMeetingsFromAPI();
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем наличие элементов перед инициализацией
    const meetingsList = document.getElementById('meetingsList');
    if (meetingsList) {
        loadMeetingsFromAPI();
        // Обновляем список встреч каждые 30 секунд
        setInterval(loadMeetingsFromAPI, 30000);
    } else {
        console.warn('Секция встреч не найдена. Добавьте HTML элементы для отображения встреч.');
    }
});