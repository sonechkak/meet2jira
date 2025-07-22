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

// Обработчики событий
fileInput.addEventListener('change', processFile);

// Drag & Drop
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);

function handleDragOver(e) {
    e.preventDefault();
    if (!isProcessing) {
        uploadArea.classList.add('dragover');
    }
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    if (isProcessing) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        processFile();
    }
}

// Обработка файла
async function processFile() {
    const file = fileInput.files[0];
    if (!file) return;

    // Проверка типа файла
    const allowedTypes = [
        'text/plain',
        'text/markdown',
        'text/x-markdown',
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/tiff',
        'image/bmp'
    ];

    const allowedExtensions = ['.txt', '.md', '.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'];

    // Проверяем и по MIME типу и по расширению для надежности
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    const isValidType = allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);

    if (!isValidType) {
        showMessage('Неподдерживаемый формат файла. Используйте PDF, DOCX, TXT, MD или изображения (JPG, PNG, TIFF, BMP).', 'error');
        return;
    }

    setProcessingState(true);
    clearMessage();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/file/process', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // Обрабатываем результат в формате твоего API
            showResult({
                summary: result.summary,
                document_name: result.document_name,
                model: result.model
            });
            showMessage('Документ успешно обработан!', 'success');
        } else {
            throw new Error(result.detail || 'Ошибка обработки документа');
        }
    } catch (error) {
        showMessage(`Ошибка: ${error.message}`, 'error');
        console.error('Processing error:', error);
    } finally {
        setProcessingState(false);
        fileInput.value = '';
    }
}

// Управление состоянием обработки
function setProcessingState(processing) {
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
}

// Показ результата с определением типа файла
function showResult(result) {
    // Определяем иконку по типу файла
    const fileName = result.document_name.toLowerCase();
    let fileIcon = '📄';

    if (fileName.endsWith('.pdf')) fileIcon = '📕';
    else if (fileName.endsWith('.docx')) fileIcon = '📘';
    else if (fileName.endsWith('.txt')) fileIcon = '📝';
    else if (fileName.endsWith('.md')) fileIcon = '📋';
    else if (fileName.match(/\.(jpg|jpeg|png|tiff|bmp)$/)) fileIcon = '🖼️';

    let summaryContent = result.summary;
    if (Array.isArray(summaryContent)) {
        summaryContent = summaryContent.join('\n');
    } else if (typeof summaryContent === 'object' && summaryContent !== null) {
        summaryContent = JSON.stringify(summaryContent, null, 2);
    }

    const resultId = `result-${Date.now()}`;
    const summaryId = `summary-${Date.now()}`;

    const resultHTML = `
        <div class="result-card" id="${resultId}">
            <div class="result-header">
                <div class="document-name">${fileIcon} ${escapeHtml(result.document_name)}</div>
                <div class="model-badge">🤖 ${result.model}</div>
            </div>
            
            <div class="summary-label">Создаем задачи:</div>
            <div class="summary-content" id="${summaryId}">
                ${escapeHtml(summaryContent).replace(/\n/g, '<br>')}
            </div>
            
            <div class="action-buttons">
                <button class="copy-btn" onclick="copySummary('${summaryId}')">
                    📋 Копировать список задач
                </button>
                <button class="accept-btn" onclick="acceptResult('${resultId}')">
                    ✅ Accept
                </button>
                <button class="reject-btn" onclick="rejectResult('${resultId}')">
                    ❌ Reject
                </button>
            </div>
            
            <div class="status-indicator" id="status-${resultId}" style="display: none;"></div>
        </div>
    `;

    resultsList.innerHTML = resultHTML + resultsList.innerHTML;
    resultsSection.style.display = 'block';

    // Плавная прокрутка к результатам
    setTimeout(() => {
        resultsSection.scrollIntoView({behavior: 'smooth', block: 'start'});
    }, 100);
}

// Копирование списка задач
function copySummary(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent || element.innerText;

    navigator.clipboard.writeText(text).then(() => {
        showMessage('Список задач скопирован в буфер обмена!', 'success');
    }).catch(() => {
        // Fallback для старых браузеров
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showMessage('Список задач скопирован в буфер обмена!', 'success');
    });
}

// Принятие результата
function acceptResult(resultId) {
    const resultCard = document.getElementById(resultId);
    const statusIndicator = document.getElementById(`status-${resultId}`);
    const acceptBtn = resultCard.querySelector('.accept-btn');
    const rejectBtn = resultCard.querySelector('.reject-btn');

    // Визуальное обновление
    resultCard.classList.add('accepted');
    statusIndicator.innerHTML = '<div class="status-accepted">✅ Принято</div>';
    statusIndicator.style.display = 'block';

    // Деактивируем кнопки
    acceptBtn.disabled = true;
    rejectBtn.disabled = true;
    acceptBtn.style.opacity = '0.5';
    rejectBtn.style.opacity = '0.5';

    showMessage('Результат принят!', 'success');

    // Здесь можно добавить отправку на сервер
    sendResultStatus(resultId, 'accepted');
}

// Отклонение результата
function rejectResult(resultId) {
    const resultCard = document.getElementById(resultId);
    const statusIndicator = document.getElementById(`status-${resultId}`);
    const acceptBtn = resultCard.querySelector('.accept-btn');
    const rejectBtn = resultCard.querySelector('.reject-btn');

    // Визуальное обновление
    resultCard.classList.add('rejected');
    statusIndicator.innerHTML = '<div class="status-rejected">❌ Отклонено</div>';
    statusIndicator.style.display = 'block';

    // Деактивируем кнопки
    acceptBtn.disabled = true;
    rejectBtn.disabled = true;
    acceptBtn.style.opacity = '0.5';
    rejectBtn.style.opacity = '0.5';

    showMessage('Результат отклонен', 'error');

    sendResultStatus(resultId, 'rejected');
}

// Отправка статуса на сервер (опционально)
async function sendResultStatus(resultId, status) {
    try {
        console.log(`Статус результата ${resultId}: ${status}`);
    } catch (error) {
        console.error('Ошибка отправки статуса:', error);
    }
}

// Показ сообщений
function showMessage(text, type) {
    message.innerHTML = `<div class="message ${type}">${text}</div>`;
    setTimeout(() => {
        if (type !== 'error') {
            clearMessage();
        }
    }, 5000);
}

function clearMessage() {
    message.innerHTML = '';
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}