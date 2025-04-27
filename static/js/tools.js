function addFieldSpecification() {
    const template = document.getElementById('field-spec-template');
    const container = document.getElementById('field-specifications');
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
}

function removeFieldSpecification(button) {
    const fieldSpec = button.closest('.field-specification');
    fieldSpec.remove();
}

function getFieldSpecifications() {
    const specs = [];
    const fieldSpecs = document.querySelectorAll('.field-specification');

    fieldSpecs.forEach(spec => {
        const fieldName = spec.querySelector('[name="field_name"]').value;
        const fieldType = spec.querySelector('[name="field_type"]').value;
        const fieldDescription = spec.querySelector('[name="field_description"]').value;

        if (fieldName && fieldType) {
            specs.push({
                name: fieldName,
                type: fieldType,
                description: fieldDescription || ''
            });
        }
    });

    return specs;
}

function updateProgress(message, isError = false) {
    const progressContainer = document.getElementById('progress-container');
    const currentStep = progressContainer.querySelector('.current-step');
    const stepHistory = progressContainer.querySelector('.step-history');
    const timestamp = new Date().toLocaleTimeString();

    // Move current message to history if it exists and isn't the initial message
    const currentMessage = currentStep.querySelector('.step-message')?.textContent;
    if (currentMessage && currentMessage !== 'Initializing extraction...') {
        const historyItem = document.createElement('div');
        historyItem.className = 'step completed';
        historyItem.innerHTML = `
            <div class="step-icon">✅</div>
            <div class="step-content">
                <div class="step-message">${currentMessage}</div>
                <div class="step-time">${currentStep.querySelector('.step-time').textContent}</div>
            </div>
        `;
        stepHistory.insertBefore(historyItem, stepHistory.firstChild);
    }

    // Update current step
    if (isError) {
        currentStep.innerHTML = `
            <div class="step-icon">⚠️</div>
            <div class="step-content">
                <div class="step-message error">${message}</div>
                <div class="step-time">${timestamp}</div>
            </div>
        `;
    } else {
        currentStep.innerHTML = `
            <div class="step-icon">⚙️</div>
            <div class="step-content">
                <div class="step-message">${message}</div>
                <div class="step-time">${timestamp}</div>
            </div>
        `;
    }

    progressContainer.style.display = 'block';
}

document.getElementById('enhanced-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData();
    const file = document.getElementById('file_input').files[0];
    const urlColumn = document.getElementById('url_column').value;
    const prompt = document.getElementById('file_prompt_user').value;
    const fieldSpecs = getFieldSpecifications();

    if (!file || !urlColumn || !prompt) {
        document.getElementById('validation-error').textContent = 'Please fill in all required fields';
        document.getElementById('validation-error').style.display = 'block';
        return;
    }

    if (fieldSpecs.length === 0) {
        document.getElementById('validation-error').textContent = 'Please add at least one field specification';
        document.getElementById('validation-error').style.display = 'block';
        return;
    }

    formData.append('file', file);
    formData.append('url_column', urlColumn);
    formData.append('prompt_user', prompt);
    formData.append('field_specifications', JSON.stringify(fieldSpecs.map(spec => ({
        field_name: spec.name,
        field_type: spec.type,
        description: spec.description
    }))));

    document.getElementById('validation-error').style.display = 'none';
    const progressContainer = document.getElementById('progress-container');
    progressContainer.style.display = 'block';
    updateProgress('Initializing extraction...');

    try {
        // Close any existing EventSource
        if (window.eventSource) {
            window.eventSource.close();
        }

        // Start listening for progress updates first
        window.eventSource = new EventSource('/api/progress');
        window.eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (data.message) {
                    updateProgress(data.message);
                }
                if (data.status === 'completed') {
                    window.eventSource.close();
                    updateProgress('Extraction completed successfully!');
                }
            } catch (e) {
                console.error('Error parsing SSE message:', e);
            }
        };

        window.eventSource.onerror = function(error) {
            console.error('SSE Error:', error);
            window.eventSource.close();
            updateProgress('Error: Connection to progress updates lost', true);
        };

        // Now send the actual request
        updateProgress('Uploading file and starting extraction...');
        const response = await fetch('/api/extract/enhanced', {
            method: 'POST',
            body: formData
        });

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.message || 'Server error occurred');
        }

        if (responseData.redirect) {
            updateProgress('Extraction completed! Redirecting...');
            setTimeout(() => {
                window.location.href = responseData.redirect;
            }, 1000); // Give user a chance to see the completion message
        }

    } catch (error) {
        console.error('Error:', error);
        if (window.eventSource) {
            window.eventSource.close();
        }
        updateProgress('An error occurred during extraction: ' + error.message, true);
    }
});