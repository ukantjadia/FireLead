document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    const progressStates = {
        firecrawl: { active: false, history: [] },
        enhanced: { active: false, history: [] }
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            contents.forEach(content => {
                content.style.display = 'none';
            });

            document.getElementById(`${tab.dataset.tab}-content`).style.display = 'block';
        });
    });

    // Field specification functionality
    let fieldCount = 0;

    window.addFieldSpecification = function() {
        const template = document.getElementById('field-spec-template');
        const clone = template.content.cloneNode(true);
        const container = document.getElementById('field-specifications');
        
        // Update IDs to be unique
        const newField = clone.querySelector('.field-specification');
        newField.id = `field-${fieldCount}`;
        
        container.appendChild(clone);
        fieldCount++;
    };

    window.removeFieldSpecification = function(button) {
        const fieldSpec = button.closest('.field-specification');
        if (fieldSpec) {
            fieldSpec.remove();
        }
    };

    // Event Source for progress updates
    let eventSource = null;

    function updateProgress(message, containerId, isError = false) {
        const container = document.getElementById(containerId);
        const currentStep = container.querySelector('.current-step');
        const stepHistory = container.querySelector('.step-history');
        const timestamp = new Date().toLocaleTimeString();
        const toolType = containerId.replace('-progress', '');

        // Move current message to history if it exists
        const currentMessage = currentStep.querySelector('.step-message')?.textContent;
        if (currentMessage && currentMessage !== 'Initializing...') {
            const historyItem = document.createElement('div');
            historyItem.className = 'step completed';
            historyItem.innerHTML = `
                <div class="step-icon">✓</div>
                <div class="step-content">
                    <div class="step-message">${currentMessage}</div>
                    <div class="step-time">${currentStep.querySelector('.step-time').textContent}</div>
                </div>
            `;
            stepHistory.appendChild(historyItem);
            progressStates[toolType].history.push({
                message: currentMessage,
                timestamp: currentStep.querySelector('.step-time').textContent
            });
        }

        // Update current step
        currentStep.innerHTML = `
            <div class="step-icon">${isError ? '⚠️' : '⚙️'}</div>
            <div class="step-content">
                <div class="step-message">${message}</div>
                <div class="step-time">${timestamp}</div>
            </div>
        `;

        if (message.toLowerCase().includes('done') || message.toLowerCase().includes('error') || isError) {
            enableForm(toolType);
        }
    }

    function startProgressMonitoring(containerId) {
        if (eventSource) {
            eventSource.close();
        }

        const container = document.getElementById(containerId);
        container.style.display = 'block';
        const toolType = containerId.replace('-progress', '');
        
        // Restore previous history if exists
        if (progressStates[toolType].history.length > 0) {
            const stepHistory = container.querySelector('.step-history');
            stepHistory.innerHTML = progressStates[toolType].history.map(item => `
                <div class="step completed">
                    <div class="step-icon">✓</div>
                    <div class="step-content">
                        <div class="step-message">${item.message}</div>
                        <div class="step-time">${item.timestamp}</div>
                    </div>
                </div>
            `).join('');
        }

        eventSource = new EventSource('/api/progress');
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateProgress(data.message, containerId);
        };

        eventSource.onerror = function() {
            eventSource.close();
            eventSource = null;
            updateProgress('Error: Connection lost', containerId, true);
        };
    }

    function disableForm(toolType) {
        const form = document.getElementById(`${toolType}-form`);
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
        progressStates[toolType].active = true;
    }

    function enableForm(toolType) {
        const form = document.getElementById(`${toolType}-form`);
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Start Extraction';
        progressStates[toolType].active = false;
    }

    // Lead Score Modal
    const scoreInfoModal = document.getElementById('scoreInfoModal');
    const scoreInfoButton = document.querySelector('.score-info');
    const closeButton = document.querySelector('.close');

    if (scoreInfoButton) {
        scoreInfoButton.addEventListener('click', () => {
            scoreInfoModal.style.display = 'block';
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', () => {
            scoreInfoModal.style.display = 'none';
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target === scoreInfoModal) {
            scoreInfoModal.style.display = 'none';
        }
    });

    // Lead Scoring Function
    function calculateLeadScore(data) {
        let score = 0;
        const weights = {
            company_size: 20,
            digital_presence: 15,
            contact_info: 25,
            tech_stack: 20,
            content: 20
        };

        // Company Size Score (20%)
        if (data.company_size) {
            const sizeScore = {
                '1-10': 5,
                '11-50': 10,
                '51-200': 15,
                '201-500': 18,
                '501+': 20
            };
            score += sizeScore[data.company_size] || 10;
        }

        // Digital Presence Score (15%)
        let digitalScore = 0;
        if (data.linkedin_company_url) digitalScore += 5;
        if (data.twitter_url) digitalScore += 3;
        if (data.blog_page_detected) digitalScore += 4;
        if (data.pricing_page_detected) digitalScore += 3;
        score += digitalScore;

        // Contact Information Score (25%)
        let contactScore = 0;
        if (data.email) contactScore += 10;
        if (data.phone_number) contactScore += 8;
        if (data.contact_name) contactScore += 7;
        score += contactScore;

        // Technology Stack Score (20%)
        if (data.tech_stack) {
            const techCount = data.tech_stack.split(',').length;
            score += Math.min(techCount * 2, 20);
        }

        // Content Richness Score (20%)
        let contentScore = 0;
        if (data.description && data.description.length > 100) contentScore += 5;
        if (data.services_offered) contentScore += 5;
        if (data.product_list) contentScore += 5;
        if (data.recent_news) contentScore += 5;
        score += contentScore;

        return Math.min(Math.round(score), 100);
    }

    // Firecrawl form submission
    const firecrawlForm = document.getElementById('firecrawl-form');
    firecrawlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        if (progressStates.firecrawl.active) return;

        const prompt = document.getElementById('prompt_user').value;
        
        // Get all field checkboxes
        const fields = [
            'company_name', 'funding', 'industry', 'company_size', 'revenue_range',
            'headquarters', 'website_url', 'founding_year', 'description', 'tech_stack',
            'linkedin_company_url', 'twitter_url', 'contact_name', 'email', 'email_type',
            'phone_number', 'source_url', 'page_title', 'date_scraped', 'lead_score',
            'recent_news', 'services_offered', 'product_list', 'cta_type',
            'pricing_page_detected', 'blog_page_detected'
        ];

        // Create selected_fields object
        const selected_fields = {};
        fields.forEach(field => {
            const checkbox = document.getElementById(field);
            if (checkbox) {
                selected_fields[field] = checkbox.checked;
            }
        });

        // Validate form
        if (!prompt) {
            alert('Please enter a prompt');
            return;
        }

        if (!Object.values(selected_fields).some(Boolean)) {
            alert('Please select at least one field to extract');
            return;
        }

        try {
            disableForm('firecrawl');
            startProgressMonitoring('firecrawl-progress');

            const response = await fetch('/api/extract/firecrawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt_user: prompt,
                    selected_fields: selected_fields
                })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to start extraction');
            }

            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } catch (error) {
            updateProgress(`Error: ${error.message}`, 'firecrawl-progress', true);
            enableForm('firecrawl');
        }
    });

    // Enhanced form submission
    const enhancedForm = document.getElementById('enhanced-form');
    enhancedForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        if (progressStates.enhanced.active) return;

        const fileInput = document.getElementById('file_input');
        const urlColumn = document.getElementById('url_column').value;
        const prompt = document.getElementById('file_prompt_user').value;

        if (!fileInput.files.length) {
            alert('Please select a file');
            return;
        }

        // Collect field specifications
        const fieldSpecs = [];
        const fieldElements = document.querySelectorAll('.field-specification');
        
        fieldElements.forEach(spec => {
            const fieldName = spec.querySelector('[name="field_name"]').value.trim();
            const fieldType = spec.querySelector('[name="field_type"]').value;
            const description = spec.querySelector('[name="field_description"]').value.trim();

            if (fieldName && fieldType) {
                fieldSpecs.push({
                    field_name: fieldName,
                    field_type: fieldType,
                    description: description || fieldName // Use field name as description if not provided
                });
            }
        });

        try {
            disableForm('enhanced');
            startProgressMonitoring('enhanced-progress');

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('url_column', urlColumn);
            formData.append('prompt_user', prompt);
            formData.append('field_specifications', JSON.stringify(fieldSpecs));

            const response = await fetch('/api/extract/enhanced', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to start extraction');
            }

            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } catch (error) {
            updateProgress(`Error: ${error.message}`, 'enhanced-progress', true);
            enableForm('enhanced');
        }
    });

    // File preview
    document.getElementById('file_input').addEventListener('change', function(e) {
        const file = e.target.files[0];
        const preview = document.getElementById('file-preview');
        if (file) {
            preview.innerHTML = `
                <div class="file-info">
                    <span>${file.name}</span>
                    <small>(${(file.size / 1024).toFixed(1)} KB)</small>
                </div>
            `;
        } else {
            preview.innerHTML = '';
        }
    });

    // Utility Functions
    function showProgress(message) {
        const progressContainer = document.getElementById('firecrawl-progress');
        const currentStep = progressContainer.querySelector('.current-step .step-message');
        
        progressContainer.style.display = 'block';
        currentStep.textContent = message;
    }

    function showError(message) {
        const progressContainer = document.getElementById('firecrawl-progress');
        const currentStep = progressContainer.querySelector('.current-step');
        
        progressContainer.style.display = 'block';
        currentStep.classList.add('error');
        currentStep.querySelector('.step-message').textContent = message;
    }

    function showSuccess(message) {
        const progressContainer = document.getElementById('firecrawl-progress');
        const currentStep = progressContainer.querySelector('.current-step');
        
        progressContainer.style.display = 'block';
        currentStep.classList.remove('error');
        currentStep.classList.add('success');
        currentStep.querySelector('.step-message').textContent = message;
    }

    function showDownloadButton(filename) {
        const container = document.createElement('div');
        container.className = 'download-button-container';
        
        const button = document.createElement('a');
        button.href = `/download/${filename}`;
        button.className = 'btn btn-primary';
        button.textContent = 'Download Results';
        
        container.appendChild(button);
        document.body.appendChild(container);
    }

    // Initialize tooltips
    document.addEventListener('DOMContentLoaded', () => {
        const tooltips = document.querySelectorAll('[title]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = e.target.getAttribute('title');
                document.body.appendChild(tooltip);

                const rect = e.target.getBoundingClientRect();
                tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
                tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
            });

            element.addEventListener('mouseleave', () => {
                const tooltip = document.querySelector('.tooltip');
                if (tooltip) {
                    tooltip.remove();
                }
            });
        });
    });
});
