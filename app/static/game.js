const gameOrder = [
    // 5 câu Logic
    'logic', 'logic', 'logic', 'logic', 'logic',
    // 5 câu Sáng tạo
    'creative', 'creative', 'creative', 'creative', 'creative',
    // 5 câu Kinh doanh
    'business', 'business', 'business', 'business', 'business',
    // 5 câu Ngôn ngữ
    'language', 'language', 'language', 'language', 'language'
];
let currentIndex = 0;
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
    if (currentIndex >= gameOrder.length) {
        finishGame();
        return;
    }

    const gameType = gameOrder[currentIndex];
    
    // Update UI
    document.getElementById('game-title').innerText = `Mini Game ${currentIndex + 1}: ${getGameTitle(gameType)}`;
    const progress = ((currentIndex) / gameOrder.length) * 100;
    document.getElementById('progress').style.width = `${progress}%`;
    
    // Show loading
    document.getElementById('loading-question').classList.remove('hidden');
    document.getElementById('question-container').classList.add('hidden');

    try {
        const response = await fetch('/api/generate-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game_type: gameType })
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

function getGameTitle(type) {
    const titles = {
        'logic': 'Tư duy & Logic',
        'creative': 'Sáng tạo & Thẩm mỹ',
        'business': 'Giao tiếp & Kinh doanh',
        'language': 'Ngôn ngữ & Hội nhập'
    };
    return titles[type] || type;
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
    
    currentIndex++;
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
