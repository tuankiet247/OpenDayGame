const miniGamesConfig = [
    { type: 'logic', name: 'Tư duy & Logic', count: 5 },
    { type: 'creative', name: 'Sáng tạo & Thẩm mỹ', count: 5 },
    { type: 'business', name: 'Giao tiếp & Kinh doanh', count: 5 },
    { type: 'language', name: 'Ngôn ngữ & Hội nhập', count: 5 }
];

let currentMiniGameIndex = 0;
let currentQuestionIndex = 0;
let userProfile = { name: '' };
let scores = {
    "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0
};

// UI Elements
const screens = {
    intro: document.getElementById('intro-screen'),
    profile: document.getElementById('profile-screen'),
    game: document.getElementById('game-screen'),
    result: document.getElementById('result-screen')
};

function switchScreen(screenName) {
    Object.values(screens).forEach(el => el.classList.add('hidden'));
    screens[screenName].classList.remove('hidden');
}

function startGame() {
    switchScreen('profile');
}

function submitProfile() {
    const nameInput = document.getElementById('username');
    if (!nameInput.value.trim()) {
        alert('Hãy nhập tên để chúng mình xưng hô nhé!');
        return;
    }
    userProfile.name = nameInput.value;
    switchScreen('game');
    loadQuestion();
}

async function loadQuestion() {
    if (currentMiniGameIndex >= miniGamesConfig.length) {
        finishGame();
        return;
    }

    const currentGame = miniGamesConfig[currentMiniGameIndex];
    
    // Update UI
    document.getElementById('game-title').innerText = `${currentGame.name} (Câu ${currentQuestionIndex + 1}/${currentGame.count})`;
    
    // Calculate total progress
    let totalQuestions = miniGamesConfig.reduce((a, b) => a + b.count, 0);
    let questionsDone = 0;
    for (let i = 0; i < currentMiniGameIndex; i++) questionsDone += miniGamesConfig[i].count;
    questionsDone += currentQuestionIndex;
    
    const progress = (questionsDone / totalQuestions) * 100;
    document.getElementById('progress').style.width = `${progress}%`;
    
    // Show loading
    document.getElementById('loading-question').classList.remove('hidden');
    document.getElementById('question-container').classList.add('hidden');

    try {
        const response = await fetch('/api/generate-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game_type: currentGame.type })
        });
        
        const data = await response.json();
        renderQuestion(data);
    } catch (error) {
        console.error('Error:', error);
        alert('Có lỗi kết nối với máy chủ AI.');
    } finally {
        document.getElementById('loading-question').classList.add('hidden');
        document.getElementById('question-container').classList.remove('hidden');
    }
}

function renderQuestion(data) {
    document.getElementById('question-text').innerText = data.question;
    const optionsList = document.getElementById('options-list');
    optionsList.innerHTML = '';

    data.options.forEach(opt => {
        const div = document.createElement('div');
        div.className = 'option-card';
        div.innerText = `${opt.id}. ${opt.text}`;
        div.onclick = () => selectOption(opt.scores);
        optionsList.appendChild(div);
    });
}

function selectOption(points) {
    // Add scores
    for (const [major, score] of Object.entries(points)) {
        if (scores[major] !== undefined) {
            scores[major] += score;
        }
    }
    
    currentQuestionIndex++;
    if (currentQuestionIndex >= miniGamesConfig[currentMiniGameIndex].count) {
        currentMiniGameIndex++;
        currentQuestionIndex = 0;
    }
    loadQuestion();
}

async function finishGame() {
    switchScreen('result');
    document.getElementById('loading-result').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/submit-result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                scores: scores,
                user_profile: userProfile
            })
        });

        const result = await response.json();
        renderResult(result);
    } catch (error) {
        console.error(error);
        alert('Lỗi khi lấy kết quả.');
    }
}

function renderResult(data) {
    document.getElementById('loading-result').classList.add('hidden');
    document.getElementById('result-content').classList.remove('hidden');
    
    document.getElementById('top-major').innerText = data.top_major;
    document.getElementById('reasoning').innerText = data.reasoning;
    document.getElementById('backup-majors').innerText = data.backup_majors.join(', ');
    document.getElementById('roadmap').innerText = data.roadmap;
    document.getElementById('career').innerText = data.career_opportunities;

    const badgeContainer = document.getElementById('badges-container');
    badgeContainer.innerHTML = '';
    if (data.badges) {
        data.badges.forEach(badge => {
            const span = document.createElement('span');
            span.className = 'badge';
            span.innerText = badge;
            badgeContainer.appendChild(span);
        });
    }
}
