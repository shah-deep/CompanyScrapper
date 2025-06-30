// Extracted from index.html <script> block
// (Paste the entire JS code from the <script>...</script> block here, without the tags) 

// ============================================================================
// VALIDATION MODULE
// ============================================================================
const Validation = {
    // URL validation - must start with http:// or https://
    validateUrl(url) {
        if (!url || typeof url !== 'string') return false;
        const trimmed = url.trim();
        return trimmed.startsWith('http://') || trimmed.startsWith('https://');
    },

    // Team ID validation - alphanumeric, underscore, dash only, no spaces
    validateTeamId(teamId) {
        if (!teamId || typeof teamId !== 'string') return false;
        const trimmed = teamId.trim();
        if (trimmed.length === 0) return false;
        // Only allow alphanumeric, underscore, and dash characters
        const validPattern = /^[a-zA-Z0-9_-]+$/;
        return validPattern.test(trimmed);
    },

    // Form validation functions
    validateCrawlerForm() {
        const companyUrl = document.getElementById('companyUrl').value.trim();
        const teamId = document.getElementById('teamId').value.trim().toLowerCase();
        const isValid = this.validateUrl(companyUrl) && this.validateTeamId(teamId) && !UIState.isCrawlerRunning;
        
        document.getElementById('startCrawlBtn').disabled = !isValid;
        return isValid;
    },

    validateScrapperForm() {
        const teamId = document.getElementById('scrapeTeamId').value.trim().toLowerCase();
        const isValid = this.validateTeamId(teamId) && !UIState.isScraperRunning;
        
        document.getElementById('startScrapeBtn').disabled = !isValid;
        return isValid;
    },

    validateDataForm() {
        const teamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        const isValid = this.validateTeamId(teamId);
        
        document.getElementById('getUrlsBtn').disabled = !isValid;
        document.getElementById('getDataBtn').disabled = !isValid;
        return isValid;
    },

    validateDownloadButtons() {
        const crawlerTeamId = document.getElementById('teamId').value.trim().toLowerCase();
        const dataTeamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        
        document.getElementById('downloadUrlsBtn').disabled = !this.validateTeamId(crawlerTeamId);
        document.getElementById('downloadUrlsDataBtn').disabled = !this.validateTeamId(dataTeamId);
    },

    validateDeleteButtons() {
        const crawlerTeamId = document.getElementById('teamId').value.trim().toLowerCase();
        const dataTeamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        
        document.getElementById('deleteUrlsBtn').disabled = !this.validateTeamId(crawlerTeamId);
        document.getElementById('deleteUrlsDataBtn').disabled = !this.validateTeamId(dataTeamId);
    },

    validateRefreshButton() {
        const teamId = document.getElementById('teamId').value.trim().toLowerCase();
        document.getElementById('refreshUrlsBtn').disabled = !this.validateTeamId(teamId);
    },

    // Initialize all button states
    initializeButtonStates() {
        this.validateCrawlerForm();
        this.validateScrapperForm();
        this.validateDataForm();
        this.validateDownloadButtons();
        this.validateDeleteButtons();
        this.validateRefreshButton();
    }
};

// ============================================================================
// UI STATE MANAGEMENT
// ============================================================================
const UIState = {
    currentTaskId: null,
    taskCheckInterval: null,
    isCrawlerRunning: false,
    isScraperRunning: false,

    setCrawlerRunning(running) {
        this.isCrawlerRunning = running;
        Validation.validateCrawlerForm();
    },

    setScraperRunning(running) {
        this.isScraperRunning = running;
        Validation.validateScrapperForm();
    },

    clearTaskInterval() {
        if (this.taskCheckInterval) {
            clearInterval(this.taskCheckInterval);
            this.taskCheckInterval = null;
        }
    }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================
const Utils = {
    showAlert(message, type = 'info') {
        console.log('showAlert called with:', message, type);
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the active tab content
        const activeTab = document.querySelector('.tab-pane.active');
        if (activeTab) {
            // Insert at the beginning of the active tab
            activeTab.insertBefore(alertDiv, activeTab.firstChild);
            console.log('Alert inserted successfully in active tab');
        } else {
            // Fallback: insert at the top of the page
            const mainContainer = document.querySelector('.main-container');
            if (mainContainer) {
                mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
                console.log('Alert inserted successfully in main container');
            } else {
                console.error('Could not find suitable location for alert insertion');
            }
        }
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    },

    updateProgress(progressElement, statusElement, progress, status, type = 'info') {
        if (progressElement) {
            progressElement.style.width = progress + '%';
        }
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `status-message status-${type}`;
        }
    },

    checkTaskStatus(taskId, progressContainer, progressBar, statusElement, onComplete) {
        fetch(`/api/task/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'running') {
                    this.updateProgress(progressBar, statusElement, 50, data.progress, 'info');
                } else if (data.status === 'completed') {
                    this.updateProgress(progressBar, statusElement, 100, data.progress, 'success');
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                        if (onComplete) onComplete(data.result);
                    }, 2000);
                    UIState.clearTaskInterval();
                } else if (data.status === 'failed') {
                    this.updateProgress(progressBar, statusElement, 100, data.progress, 'error');
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                    }, 3000);
                    UIState.clearTaskInterval();
                }
            })
            .catch(error => {
                console.error('Error checking task status:', error);
                this.updateProgress(progressBar, statusElement, 100, 'Error checking status', 'error');
            });
    }
};

// ============================================================================
// FORM HANDLERS
// ============================================================================
const FormHandlers = {
    // Crawler form submission
    handleCrawlerSubmit(e) {
        e.preventDefault();
        
        if (!Validation.validateCrawlerForm()) {
            Utils.showAlert('Please fill in all required fields correctly. Team ID can only contain letters, numbers, underscores, and dashes.', 'warning');
            return;
        }
        
        const formData = {
            company_url: document.getElementById('companyUrl').value,
            team_id: document.getElementById('teamId').value.trim().toLowerCase(),
            additional_input: document.getElementById('additionalUrls').value,
            skip_words: document.getElementById('skipWords').value,
            max_pages: parseInt(document.getElementById('maxPages').value),
            skip_external: document.getElementById('skipExternal').checked
        };

        fetch('/api/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                UIState.currentTaskId = data.task_id;
                UIState.setCrawlerRunning(true);
                document.getElementById('crawlerProgress').style.display = 'block';
                
                UIState.taskCheckInterval = setInterval(() => {
                    Utils.checkTaskStatus(
                        UIState.currentTaskId,
                        document.getElementById('crawlerProgress'),
                        document.querySelector('#crawlerProgress .progress-bar'),
                        document.getElementById('crawlerStatus'),
                        (result) => {
                            if (result.success) {
                                ResultsDisplay.showCrawlerResults(result);
                                Utils.showAlert('Crawling completed successfully!', 'success');
                            } else {
                                Utils.showAlert('Crawling failed: ' + result.error, 'danger');
                            }
                            UIState.setCrawlerRunning(false);
                        }
                    );
                }, 1000);
            } else {
                Utils.showAlert('Failed to start crawling: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Utils.showAlert('Error starting crawling process', 'danger');
            UIState.setCrawlerRunning(false);
        });
    },

    // Scrapper form submission
    handleScrapperSubmit(e) {
        e.preventDefault();
        
        if (!Validation.validateScrapperForm()) {
            Utils.showAlert('Please fill in all required fields correctly. Team ID can only contain letters, numbers, underscores, and dashes.', 'warning');
            return;
        }
        
        const formData = {
            team_id: document.getElementById('scrapeTeamId').value.trim().toLowerCase(),
            user_id: document.getElementById('userId').value,
            additional_input: document.getElementById('scrapeAdditionalUrls').value,
            skip_existing_urls: document.getElementById('skipExistingUrls').checked,
            iterative: document.getElementById('iterative').checked,
            processing_mode: document.getElementById('processingMode').value
        };

        fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                UIState.currentTaskId = data.task_id;
                UIState.setScraperRunning(true);
                document.getElementById('scrapeProgress').style.display = 'block';
                
                UIState.taskCheckInterval = setInterval(() => {
                    Utils.checkTaskStatus(
                        UIState.currentTaskId,
                        document.getElementById('scrapeProgress'),
                        document.querySelector('#scrapeProgress .progress-bar'),
                        document.getElementById('scrapeStatus'),
                        (result) => {
                            if (result.success) {
                                ResultsDisplay.showScrapeResults(result);
                                Utils.showAlert('Scraping completed successfully!', 'success');
                            } else {
                                Utils.showAlert('Scraping failed: ' + result.error, 'danger');
                            }
                            UIState.setScraperRunning(false);
                        }
                    );
                }, 1000);
            } else {
                Utils.showAlert('Failed to start scraping: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Utils.showAlert('Error starting scraping process', 'danger');
            UIState.setScraperRunning(false);
        });
    }
};

// ============================================================================
// BUTTON HANDLERS
// ============================================================================
const ButtonHandlers = {
    // Get URLs button
    handleGetUrls() {
        const teamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        console.log('Get URLs clicked for team ID:', teamId);
        
        if (!Validation.validateTeamId(teamId)) {
            Utils.showAlert('Please enter a valid Team ID (letters, numbers, underscores, and dashes only)', 'warning');
            return;
        }

        // Disable button during request
        document.getElementById('getUrlsBtn').disabled = true;

        fetch(`/api/urls/${teamId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Get URLs response:', data);
                if (data.success) {
                    document.getElementById('urlsSection').style.display = 'block';
                    // Render URLs as a list for better readability
                    const urlsContent = document.getElementById('urlsContent');
                    const urls = (data.content || '').split(/\r?\n|,|\s+/).filter(Boolean);
                    urlsContent.innerHTML = urls.map(url => `<div>${url}</div>`).join('');
                    Utils.showAlert(`Retrieved ${data.url_count} URLs from file`, 'success');
                } else {
                    // Check if it's a "no data found" error
                    console.log('Error message:', data.error);
                    if (data.error && data.error.includes('No URL file found')) {
                        console.log('Showing "No data was found" alert');
                        Utils.showAlert('No data was found for this Team ID', 'warning');
                    } else {
                        console.log('Showing original error alert');
                        Utils.showAlert(data.error, 'warning');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Utils.showAlert('Error retrieving URLs', 'danger');
            })
            .finally(() => {
                Validation.validateDataForm(); // Re-enable button if valid
            });
    },

    // Get Data button
    handleGetData() {
        const teamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        console.log('Get Data clicked for team ID:', teamId);
        
        if (!Validation.validateTeamId(teamId)) {
            Utils.showAlert('Please enter a valid Team ID (letters, numbers, underscores, and dashes only)', 'warning');
            return;
        }

        // Disable button during request
        document.getElementById('getDataBtn').disabled = true;

        fetch(`/api/data/${teamId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Get Data response:', data);
                if (data.success) {
                    document.getElementById('dataSection').style.display = 'block';
                    // Use jsonview jQuery plugin for interactive JSON display
                    $('#dataContent').empty().JSONView(data.data, { collapsed: true });
                    Utils.showAlert(`Retrieved ${data.data.total_items} knowledge items`, 'success');
                } else {
                    // Check if it's a "no data found" error
                    console.log('Error message:', data.error);
                    if (data.error && data.error.includes('No knowledge data found')) {
                        console.log('Showing "No data was found" alert');
                        Utils.showAlert('No data was found for this Team ID', 'warning');
                    } else {
                        console.log('Showing original error alert');
                        Utils.showAlert(data.error, 'warning');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Utils.showAlert('Error retrieving data', 'danger');
            })
            .finally(() => {
                Validation.validateDataForm(); // Re-enable button if valid
            });
    },

    // Download buttons
    handleDownloadUrls() {
        const teamId = document.getElementById('teamId').value.trim().toLowerCase();
        if (Validation.validateTeamId(teamId)) {
            window.open(`/api/download/${teamId}`, '_blank');
        }
    },

    handleDownloadUrlsData() {
        const teamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        if (Validation.validateTeamId(teamId)) {
            window.open(`/api/download/${teamId}`, '_blank');
        }
    },

    // Refresh button
    handleRefreshUrls() {
        const teamId = document.getElementById('teamId').value.trim().toLowerCase();
        if (Validation.validateTeamId(teamId)) {
            // Disable button during request
            document.getElementById('refreshUrlsBtn').disabled = true;

            fetch(`/api/urls/${teamId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Render URLs as a list for better readability
                        const urlFileContent = document.getElementById('urlFileContent');
                        const urls = (data.content || '').split(/\r?\n|,|\s+/).filter(Boolean);
                        urlFileContent.innerHTML = urls.map(url => `<div>${url}</div>`).join('');
                        Utils.showAlert('URL file refreshed', 'success');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    Utils.showAlert('Error refreshing URLs', 'danger');
                })
                .finally(() => {
                    Validation.validateRefreshButton(); // Re-enable button if valid
                });
        }
    },

    // Delete buttons
    handleDeleteUrls() {
        const teamId = document.getElementById('teamId').value.trim().toLowerCase();
        if (Validation.validateTeamId(teamId)) {
            if (confirm(`Are you sure you want to delete all files for team "${teamId}"? This action cannot be undone.`)) {
                // Disable button during request
                document.getElementById('deleteUrlsBtn').disabled = true;

                fetch(`/api/delete/${teamId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Utils.showAlert(`Successfully deleted: ${data.deleted_files.join(', ')}`, 'success');
                        // Clear the URL file content display
                        document.getElementById('urlFileContent').innerHTML = '';
                        document.getElementById('crawlerResults').style.display = 'none';
                    } else {
                        Utils.showAlert('Delete failed: ' + data.error, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    Utils.showAlert('Error deleting files', 'danger');
                })
                .finally(() => {
                    Validation.validateDeleteButtons(); // Re-enable button if valid
                });
            }
        }
    },

    handleDeleteUrlsData() {
        const teamId = document.getElementById('dataTeamId').value.trim().toLowerCase();
        if (Validation.validateTeamId(teamId)) {
            if (confirm(`Are you sure you want to delete all files for team "${teamId}"? This action cannot be undone.`)) {
                // Disable button during request
                document.getElementById('deleteUrlsDataBtn').disabled = true;

                fetch(`/api/delete/${teamId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Utils.showAlert(`Successfully deleted: ${data.deleted_files.join(', ')}`, 'success');
                        // Clear the displays
                        document.getElementById('urlsContent').innerHTML = '';
                        document.getElementById('dataContent').innerHTML = '';
                        document.getElementById('urlsSection').style.display = 'none';
                        document.getElementById('dataSection').style.display = 'none';
                    } else {
                        Utils.showAlert('Delete failed: ' + data.error, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    Utils.showAlert('Error deleting files', 'danger');
                })
                .finally(() => {
                    Validation.validateDeleteButtons(); // Re-enable button if valid
                });
            }
        }
    }
};

// ============================================================================
// RESULTS DISPLAY
// ============================================================================
const ResultsDisplay = {
    showCrawlerResults(result) {
        const metrics = result.summary;
        const metricsHtml = `
            <div class="col-md-4">
                <div class="metric-card">
                    <div class="metric-value">${metrics.total_unique_urls || 0}</div>
                    <div class="metric-label">Total URLs</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="metric-card">
                    <div class="metric-value">${metrics.company_pages || 0}</div>
                    <div class="metric-label">Company Pages</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="metric-card">
                    <div class="metric-value">${metrics.blog_posts || 0}</div>
                    <div class="metric-label">Blog Posts</div>
                </div>
            </div>
        `;
        document.getElementById('crawlerMetrics').innerHTML = metricsHtml;
        document.getElementById('crawlerResults').style.display = 'block';
        
        // Load URL file content
        const teamId = document.getElementById('teamId').value.trim().toLowerCase();
        fetch(`/api/urls/${teamId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Render URLs as a list for better readability
                    const urlFileContent = document.getElementById('urlFileContent');
                    const urls = (data.content || '').split(/\r?\n|,|\s+/).filter(Boolean);
                    urlFileContent.innerHTML = urls.map(url => `<div>${url}</div>`).join('');
                }
            });
    },

    showScrapeResults(result) {
        const stats = result.statistics;
        const metricsHtml = `
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value">${stats.urls_processed || 0}</div>
                    <div class="metric-label">URLs Processed</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value">${stats.knowledge_items_saved || 0}</div>
                    <div class="metric-label">Knowledge Items</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value">${stats.iterations_completed || 0}</div>
                    <div class="metric-label">Iterations</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value">${stats.total_new_links_found || 0}</div>
                    <div class="metric-label">New Links</div>
                </div>
            </div>
        `;
        document.getElementById('scrapeMetrics').innerHTML = metricsHtml;
        document.getElementById('scrapeResults').style.display = 'block';
    }
};

// ============================================================================
// EVENT LISTENERS
// ============================================================================
const EventListeners = {
    initialize() {
        // Initialize button states
        Validation.initializeButtonStates();

        // Form submissions
        document.getElementById('crawlerForm').addEventListener('submit', FormHandlers.handleCrawlerSubmit);
        document.getElementById('scrapperForm').addEventListener('submit', FormHandlers.handleScrapperSubmit);

        // Button clicks
        document.getElementById('getUrlsBtn').addEventListener('click', ButtonHandlers.handleGetUrls);
        document.getElementById('getDataBtn').addEventListener('click', ButtonHandlers.handleGetData);
        document.getElementById('downloadUrlsBtn').addEventListener('click', ButtonHandlers.handleDownloadUrls);
        document.getElementById('downloadUrlsDataBtn').addEventListener('click', ButtonHandlers.handleDownloadUrlsData);
        document.getElementById('refreshUrlsBtn').addEventListener('click', ButtonHandlers.handleRefreshUrls);
        document.getElementById('deleteUrlsBtn').addEventListener('click', ButtonHandlers.handleDeleteUrls);
        document.getElementById('deleteUrlsDataBtn').addEventListener('click', ButtonHandlers.handleDeleteUrlsData);

        // Form field listeners for validation
        this.setupFormValidationListeners();
    },

    setupFormValidationListeners() {
        // Crawler form field listeners
        document.getElementById('companyUrl').addEventListener('input', () => Validation.validateCrawlerForm());
        document.getElementById('teamId').addEventListener('input', (e) => {
            e.target.value = e.target.value.toLowerCase();
            Validation.validateCrawlerForm();
            Validation.validateDownloadButtons();
            Validation.validateDeleteButtons();
            Validation.validateRefreshButton();
        });

        // Scrapper form field listeners
        document.getElementById('scrapeTeamId').addEventListener('input', (e) => {
            e.target.value = e.target.value.toLowerCase();
            Validation.validateScrapperForm();
        });

        // Data form field listeners
        document.getElementById('dataTeamId').addEventListener('input', (e) => {
            e.target.value = e.target.value.toLowerCase();
            Validation.validateDataForm();
            Validation.validateDownloadButtons();
            Validation.validateDeleteButtons();
        });

        // Additional form field listeners for comprehensive validation
        document.getElementById('additionalUrls').addEventListener('input', () => Validation.validateCrawlerForm());
        document.getElementById('skipWords').addEventListener('input', () => Validation.validateCrawlerForm());
        document.getElementById('maxPages').addEventListener('input', () => Validation.validateCrawlerForm());
        document.getElementById('skipExternal').addEventListener('change', () => Validation.validateCrawlerForm());
        
        document.getElementById('userId').addEventListener('input', () => Validation.validateScrapperForm());
        document.getElementById('scrapeAdditionalUrls').addEventListener('input', () => Validation.validateScrapperForm());
        document.getElementById('skipExistingUrls').addEventListener('change', () => Validation.validateScrapperForm());
        document.getElementById('iterative').addEventListener('change', () => Validation.validateScrapperForm());
        document.getElementById('processingMode').addEventListener('change', () => Validation.validateScrapperForm());
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================
// Wrap all event listeners and $ usage in a DOM-ready handler
$(function() {
    EventListeners.initialize();

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 