/**
 * Student Assistant System - Main JavaScript
 * Handles interactivity, form validation, and dynamic UI
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all components
    initNavigation();
    initFlashMessages();
    initPasswordToggle();
    initFormValidation();
    initAttendanceCalculator();
    initCGPACalculator();
    initExamChecker();
    initAssistantChat();
    initWhatIfPredictor();
    initCharts();
});

/**
 * Navigation
 */
function initNavigation() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userMenu = document.getElementById('userMenu');

    // Mobile menu toggle
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });
    }

    // User dropdown menu
    if (userMenuBtn && userMenu) {
        userMenuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userMenu.classList.toggle('active');
        });

        document.addEventListener('click', function (e) {
            if (!userMenuBtn.contains(e.target) && !userMenu.contains(e.target)) {
                userMenu.classList.remove('active');
            }
        });
    }
}

/**
 * Flash Messages
 */
function initFlashMessages() {
    const flashContainer = document.querySelector('.flash-container');
    if (!flashContainer) return;

    const flashes = flashContainer.querySelectorAll('.flash');
    flashes.forEach(flash => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            dismissFlash(flash);
        }, 5000);

        // Click to dismiss
        flash.addEventListener('click', () => {
            dismissFlash(flash);
        });

        // Close button
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                dismissFlash(flash);
            });
        }
    });
}

function dismissFlash(flash) {
    flash.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => flash.remove(), 300);
}

/**
 * Password Toggle
 */
function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const input = this.parentElement.querySelector('input');
            if (input.type === 'password') {
                input.type = 'text';
                this.textContent = '🙈';
            } else {
                input.type = 'password';
                this.textContent = '👁';
            }
        });
    });
}

/**
 * Form Validation
 */
function initFormValidation() {
    // Signup form validation
    const signupForm = document.querySelector('.auth-form form[action*="signup"]');
    if (signupForm) {
        signupForm.addEventListener('submit', function (e) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');

            if (password && confirmPassword) {
                if (password.value !== confirmPassword.value) {
                    e.preventDefault();
                    showError(confirmPassword, 'Passwords do not match');
                }

                if (password.value.length < 6) {
                    e.preventDefault();
                    showError(password, 'Password must be at least 6 characters');
                }
            }
        });
    }

    // Generic form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    showError(field, 'This field is required');
                }
            });

            if (!valid) e.preventDefault();
        });
    });
}

function showError(input, message) {
    // Remove existing error
    const existingError = input.parentElement.querySelector('.error-message');
    if (existingError) existingError.remove();

    // Add error styling
    input.style.borderColor = 'var(--danger)';

    // Add error message
    const error = document.createElement('span');
    error.className = 'error-message';
    error.style.color = 'var(--danger)';
    error.style.fontSize = '0.8rem';
    error.style.marginTop = '0.25rem';
    error.style.display = 'block';
    error.textContent = message;
    input.parentElement.appendChild(error);

    // Remove error on input
    input.addEventListener('input', function () {
        input.style.borderColor = '';
        const err = input.parentElement.querySelector('.error-message');
        if (err) err.remove();
    }, { once: true });
}

/**
 * Attendance Calculator
 */
function initAttendanceCalculator() {
    const form = document.getElementById('attendance-form');
    if (!form) return;

    const inputs = form.querySelectorAll('input[type="number"]');
    const previewBox = document.querySelector('.preview-box');
    const previewPercentage = document.querySelector('.preview-percentage');
    const previewBarFill = document.querySelector('.preview-bar-fill');
    const previewStatus = document.querySelector('.preview-status');

    function updatePreview() {
        const weeks = parseInt(document.getElementById('weeks')?.value) || 0;
        const classesPerWeek = parseInt(document.getElementById('classes_per_week')?.value) || 0;
        const attended = parseInt(document.getElementById('attended')?.value) || 0;

        const totalClasses = weeks * classesPerWeek;
        let percentage = 0;

        if (totalClasses > 0) {
            percentage = (attended / totalClasses) * 100;
        }

        // Update display
        if (previewPercentage) {
            previewPercentage.textContent = percentage.toFixed(1) + '%';
        }

        if (previewBarFill) {
            previewBarFill.style.width = Math.min(percentage, 100) + '%';
            previewBarFill.style.background = percentage >= 80 ? 'var(--success)' : 'var(--danger)';
        }

        if (previewBox) {
            previewBox.className = 'preview-box ' + (percentage >= 80 ? 'safe' : 'danger');
        }

        if (previewStatus) {
            if (percentage >= 80) {
                previewStatus.innerHTML = '✅ You are safe from examination bar';
            } else {
                const needed = Math.ceil((0.8 * totalClasses) - attended);
                if (needed > 0 && totalClasses > 0) {
                    previewStatus.innerHTML = `⚠️ You need ${needed} more classes to reach 80%`;
                } else {
                    previewStatus.innerHTML = '⚠️ Below 80% threshold';
                }
            }
        }
    }

    inputs.forEach(input => {
        input.addEventListener('input', updatePreview);
    });

    // Initial calculation
    updatePreview();
}

/**
 * CGPA Calculator
 */
function initCGPACalculator() {
    const gradeSelect = document.getElementById('grade');
    const marksInput = document.getElementById('marks');
    const gradePreview = document.querySelector('.grade-preview');
    const inputMethod = document.querySelectorAll('input[name="input_method"]');

    if (!marksInput) return;

    // Grade scheme for IIUM
    const gradeScheme = [
        { min: 90, grade: 'A', points: 4.00 },
        { min: 85, grade: 'A-', points: 3.67 },
        { min: 80, grade: 'B+', points: 3.33 },
        { min: 75, grade: 'B', points: 3.00 },
        { min: 70, grade: 'B-', points: 2.67 },
        { min: 65, grade: 'C+', points: 2.33 },
        { min: 60, grade: 'C', points: 2.00 },
        { min: 55, grade: 'D', points: 1.67 },
        { min: 50, grade: 'D-', points: 1.33 },
        { min: 45, grade: 'E', points: 1.00 },
        { min: 0, grade: 'F', points: 0.00 }
    ];

    function getGradeFromMarks(marks) {
        for (const g of gradeScheme) {
            if (marks >= g.min) {
                return g;
            }
        }
        return gradeScheme[gradeScheme.length - 1];
    }

    marksInput.addEventListener('input', function () {
        const marks = parseFloat(this.value) || 0;
        const gradeInfo = getGradeFromMarks(marks);

        if (gradePreview) {
            gradePreview.textContent = `Grade: ${gradeInfo.grade} (${gradeInfo.points.toFixed(2)} points)`;
            gradePreview.className = 'grade-preview grade-' + gradeInfo.grade.replace('+', 'plus').replace('-', 'minus');
        }
    });

    // Toggle input method
    inputMethod.forEach(radio => {
        radio.addEventListener('change', function () {
            const gradeGroup = document.getElementById('grade-group');
            const marksGroup = document.getElementById('marks-group');

            if (this.value === 'grade') {
                gradeGroup?.classList.remove('hidden');
                marksGroup?.classList.add('hidden');
            } else {
                gradeGroup?.classList.add('hidden');
                marksGroup?.classList.remove('hidden');
            }
        });
    });
}

/**
 * Exam Checker
 */
function initExamChecker() {
    const carryMarkInput = document.getElementById('carry_mark');
    const carryTotalInput = document.getElementById('carry_total');
    const carryPreview = document.getElementById('carry-preview');

    const finalMarkInput = document.getElementById('final_mark');
    const finalTotalInput = document.getElementById('final_total');
    const finalPreview = document.getElementById('final-preview');

    function updateCarryPreview() {
        if (!carryMarkInput || !carryTotalInput || !carryPreview) return;

        const mark = parseFloat(carryMarkInput.value) || 0;
        const total = parseFloat(carryTotalInput.value) || 40;
        const percentage = (mark / total) * 100;
        const minNeeded = total * 0.4; // 40% minimum

        if (percentage >= 40) {
            carryPreview.innerHTML = `✅ Your carry mark: ${percentage.toFixed(1)}% (Passed)`;
            carryPreview.className = 'requirement-preview';
        } else {
            const needed = minNeeded - mark;
            carryPreview.innerHTML = `⚠️ Need ${needed.toFixed(1)} more marks (${(40 - percentage).toFixed(1)}% short)`;
            carryPreview.className = 'requirement-preview danger';
        }
    }

    function updateFinalPreview() {
        if (!finalMarkInput || !finalTotalInput || !finalPreview) return;

        const mark = parseFloat(finalMarkInput.value) || 0;
        const total = parseFloat(finalTotalInput.value) || 60;
        const percentage = (mark / total) * 100;
        const minNeeded = total * 0.4; // 40% minimum

        if (percentage >= 40) {
            finalPreview.innerHTML = `✅ Your final exam: ${percentage.toFixed(1)}% (Passed)`;
            finalPreview.className = 'requirement-preview';
        } else {
            const needed = minNeeded - mark;
            finalPreview.innerHTML = `⚠️ Need ${needed.toFixed(1)} more marks (${(40 - percentage).toFixed(1)}% short)`;
            finalPreview.className = 'requirement-preview danger';
        }
    }

    if (carryMarkInput) carryMarkInput.addEventListener('input', updateCarryPreview);
    if (carryTotalInput) carryTotalInput.addEventListener('input', updateCarryPreview);
    if (finalMarkInput) finalMarkInput.addEventListener('input', updateFinalPreview);
    if (finalTotalInput) finalTotalInput.addEventListener('input', updateFinalPreview);
}

/**
 * AI Assistant Chat
 */
function initAssistantChat() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const quickQuestions = document.querySelectorAll('.chip');

    if (!chatForm || !chatInput || !chatMessages) return;

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question) return;

        // Add user message
        addMessage(question, 'user');
        chatInput.value = '';

        // Send to backend
        sendQuestion(question);
    });

    // Quick question chips
    quickQuestions.forEach(chip => {
        chip.addEventListener('click', function () {
            const question = this.textContent.trim();
            chatInput.value = question;
            chatForm.dispatchEvent(new Event('submit'));
        });
    });

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const icon = document.createElement('span');
        icon.className = 'message-icon';
        icon.textContent = type === 'user' ? '👤' : '🤖';

        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = text;

        messageDiv.appendChild(icon);
        messageDiv.appendChild(content);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendQuestion(question) {
        try {
            const response = await fetch('/assistant/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();
            addMessage(data.answer || data.error || 'Sorry, I could not process that.', 'assistant');
        } catch (error) {
            addMessage('Sorry, there was an error. Please try again.', 'assistant');
        }
    }
}

/**
 * What-If Predictor
 */
function initWhatIfPredictor() {
    const attendanceSlider = document.getElementById('what-if-attendance');
    const carrySlider = document.getElementById('what-if-carry');
    const gpaSlider = document.getElementById('what-if-gpa');
    const resultDiv = document.getElementById('predictor-result');

    if (!attendanceSlider || !carrySlider || !gpaSlider || !resultDiv) return;

    const attendanceValue = document.getElementById('attendance-value');
    const carryValue = document.getElementById('carry-value');
    const gpaValue = document.getElementById('gpa-value');

    function updatePrediction() {
        const attendance = parseFloat(attendanceSlider.value);
        const carry = parseFloat(carrySlider.value);
        const gpa = parseFloat(gpaSlider.value);

        // Update displayed values
        if (attendanceValue) attendanceValue.textContent = attendance + '%';
        if (carryValue) carryValue.textContent = carry + '%';
        if (gpaValue) gpaValue.textContent = gpa.toFixed(2);

        // Simple risk calculation
        let risk = 'Low';
        let riskClass = 'risk-low';

        if (attendance < 70 || carry < 50 || gpa < 2.0) {
            risk = 'High';
            riskClass = 'risk-high';
        } else if (attendance < 80 || carry < 60 || gpa < 2.5) {
            risk = 'Medium';
            riskClass = 'risk-medium';
        }

        resultDiv.className = `predictor-result ${riskClass}`;
        resultDiv.innerHTML = `
            <div class="result-risk">
                <span class="result-label">Predicted Risk:</span>
                <span class="result-value ${riskClass}">${risk}</span>
            </div>
        `;
    }

    attendanceSlider.addEventListener('input', updatePrediction);
    carrySlider.addEventListener('input', updatePrediction);
    gpaSlider.addEventListener('input', updatePrediction);

    // Initial prediction
    updatePrediction();
}

/**
 * Charts (using Chart.js if available)
 */
function initCharts() {
    const cgpaChartCanvas = document.getElementById('cgpa-chart');
    if (!cgpaChartCanvas || typeof Chart === 'undefined') return;

    // Get data from data attributes or inline script
    const chartDataElement = document.getElementById('chart-data');
    let labels = [];
    let data = [];

    if (chartDataElement) {
        try {
            const chartData = JSON.parse(chartDataElement.textContent);
            labels = chartData.labels || [];
            data = chartData.data || [];
        } catch (e) {
            console.error('Could not parse chart data');
        }
    }

    // Create chart
    new Chart(cgpaChartCanvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'CGPA',
                data: data,
                borderColor: '#4F46E5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#4F46E5',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 4,
                    ticks: {
                        stepSize: 0.5
                    }
                }
            }
        }
    });
}

// Add CSS animation for slideOut
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Utility function for fetching with error handling
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Export functions for use in other scripts
window.SAS = {
    showError,
    dismissFlash,
    fetchJSON
};
