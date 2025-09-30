// Demo Page Interactive JavaScript

// Demo state
let demoState = {
    isPlaying: false,
    currentQuestion: 0,
    progress: 0,
    showResults: false
};

// Interview questions
const questions = [
    {
        id: 1,
        text: "Tell me about yourself and your background in software development.",
        type: "behavioral",
        duration: 120
    },
    {
        id: 2,
        text: "Describe a challenging project you worked on and how you overcame obstacles.",
        type: "behavioral", 
        duration: 180
    },
    {
        id: 3,
        text: "How do you approach debugging complex technical issues?",
        type: "technical",
        duration: 150
    },
    {
        id: 4,
        text: "Where do you see yourself in 5 years and how does this role fit your goals?",
        type: "motivational",
        duration: 120
    }
];

let progressInterval;

// Start interview
function startInterview() {
    demoState.isPlaying = true;
    demoState.showResults = false;
    demoState.currentQuestion = 0;
    demoState.progress = 0;
    
    updateUI();
    startProgress();
    
    showToast("Interview started! AI is now conducting the interview.", "success");
}

// Pause interview
function pauseInterview() {
    demoState.isPlaying = !demoState.isPlaying;
    
    if (demoState.isPlaying) {
        startProgress();
        showToast("Interview resumed", "info");
    } else {
        stopProgress();
        showToast("Interview paused", "info");
    }
    
    updateUI();
}

// Reset interview
function resetInterview() {
    demoState.isPlaying = false;
    demoState.showResults = false;
    demoState.currentQuestion = 0;
    demoState.progress = 0;
    
    stopProgress();
    updateUI();
    hideResults();
    
    showToast("Interview reset", "info");
}

// Start progress simulation
function startProgress() {
    if (progressInterval) clearInterval(progressInterval);
    
    progressInterval = setInterval(() => {
        if (!demoState.isPlaying || demoState.showResults) return;
        
        demoState.progress += 2;
        
        if (demoState.progress >= 100) {
            if (demoState.currentQuestion < questions.length - 1) {
                // Move to next question
                demoState.currentQuestion++;
                demoState.progress = 0;
                updateQuestion();
                showToast(`Moving to question ${demoState.currentQuestion + 1}`, "info");
            } else {
                // Interview completed
                completeInterview();
            }
        }
        
        updateProgress();
        updateAnalysisMetrics();
    }, 100);
}

// Stop progress
function stopProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

// Complete interview
function completeInterview() {
    demoState.isPlaying = false;
    demoState.showResults = true;
    
    stopProgress();
    updateUI();
    showResults();
    
    showToast("Interview completed! Generating results...", "success");
}

// Update UI elements
function updateUI() {
    const statusBadge = document.getElementById('status-badge');
    const startBtn = document.getElementById('start-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const resetBtn = document.getElementById('reset-btn');
    const recordingIndicator = document.getElementById('recording-indicator');
    const aiIndicator = document.getElementById('ai-indicator');
    const candidateIndicator = document.getElementById('candidate-indicator');
    const aiStatus = document.getElementById('ai-status');
    const candidateStatus = document.getElementById('candidate-status');
    const analysisStatus = document.getElementById('analysis-status');
    
    if (demoState.showResults) {
        statusBadge.textContent = 'Completed';
        statusBadge.className = 'status-badge completed';
        startBtn.innerHTML = '<i data-lucide="rotate-ccw"></i> Start New Interview';
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        recordingIndicator.style.display = 'none';
        aiStatus.textContent = 'Complete';
        candidateStatus.textContent = 'Complete';
        analysisStatus.style.display = 'none';
        aiIndicator.className = 'indicator';
        candidateIndicator.className = 'indicator';
    } else if (demoState.isPlaying) {
        statusBadge.textContent = 'Recording';
        statusBadge.className = 'status-badge recording';
        startBtn.disabled = true;
        pauseBtn.disabled = false;
        pauseBtn.innerHTML = '<i data-lucide="pause"></i>';
        recordingIndicator.style.display = 'flex';
        aiStatus.textContent = 'Speaking';
        candidateStatus.textContent = demoState.progress > 25 ? 'Responding' : 'Listening';
        analysisStatus.style.display = 'flex';
        aiIndicator.className = 'indicator speaking';
        candidateIndicator.className = demoState.progress > 25 ? 'indicator active' : 'indicator';
    } else {
        statusBadge.textContent = 'Ready';
        statusBadge.className = 'status-badge';
        startBtn.innerHTML = '<i data-lucide="play"></i> Start Interview';
        startBtn.disabled = false;
        pauseBtn.innerHTML = '<i data-lucide="play"></i>';
        pauseBtn.disabled = !demoState.progress > 0;
        recordingIndicator.style.display = 'none';
        aiStatus.textContent = 'Ready';
        candidateStatus.textContent = 'Ready';
        analysisStatus.style.display = 'none';
        aiIndicator.className = 'indicator';
        candidateIndicator.className = 'indicator';
    }
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Update question display
function updateQuestion() {
    const questionCounter = document.getElementById('question-counter');
    const questionText = document.getElementById('question-text');
    const questionType = document.getElementById('question-type');
    
    const currentQ = questions[demoState.currentQuestion];
    
    questionCounter.textContent = `Question ${demoState.currentQuestion + 1} of ${questions.length}`;
    questionText.textContent = currentQ.text;
    questionType.textContent = currentQ.type;
}

// Update progress bar
function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    
    const totalProgress = Math.round((demoState.currentQuestion + demoState.progress/100) / questions.length * 100);
    
    progressFill.style.width = `${demoState.progress}%`;
    progressPercentage.textContent = `${totalProgress}%`;
}

// Update analysis metrics with random values
function updateAnalysisMetrics() {
    if (!demoState.isPlaying) return;
    
    const confidenceLevel = document.getElementById('confidence-level');
    const engagementScore = document.getElementById('engagement-score');
    const communicationScore = document.getElementById('communication-score');
    
    // Generate realistic random scores
    const confidence = Math.floor(Math.random() * 20) + 75;
    const engagement = Math.floor(Math.random() * 15) + 80;
    const communication = Math.floor(Math.random() * 10) + 85;
    
    confidenceLevel.textContent = `${confidence}%`;
    engagementScore.textContent = `${engagement}%`;
    communicationScore.textContent = `${communication}%`;
}

// Show results panel
function showResults() {
    const resultsPanel = document.getElementById('results-panel');
    const questionPanel = document.getElementById('question-panel');
    const progressSection = document.getElementById('progress-section');
    
    resultsPanel.style.display = 'block';
    questionPanel.style.display = 'none';
    progressSection.style.display = 'none';
    
    // Animate results appearance
    setTimeout(() => {
        resultsPanel.style.opacity = '0';
        resultsPanel.style.transform = 'translateY(20px)';
        resultsPanel.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        
        setTimeout(() => {
            resultsPanel.style.opacity = '1';
            resultsPanel.style.transform = 'translateY(0)';
        }, 50);
    }, 100);
}

// Hide results panel
function hideResults() {
    const resultsPanel = document.getElementById('results-panel');
    const questionPanel = document.getElementById('question-panel');
    const progressSection = document.getElementById('progress-section');
    
    resultsPanel.style.display = 'none';
    questionPanel.style.display = 'block';
    progressSection.style.display = 'block';
}

// Initialize demo when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateQuestion();
    updateProgress();
    updateUI();
    
    // Reset analysis metrics
    document.getElementById('confidence-level').textContent = '0%';
    document.getElementById('engagement-score').textContent = '0%';
    document.getElementById('communication-score').textContent = '0%';
});

// Handle window unload to clean up intervals
window.addEventListener('beforeunload', function() {
    stopProgress();
});