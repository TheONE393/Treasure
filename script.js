// Auto-generated Treasure Hunt script (text + image questions)
const teams = {
  "Team 1": {
    "password": "bio100",
    "questions": [
      {
        "q": "What is mitochondria?",
        "keys": [
          "Cell",
          "Ram",
          "Molecule"
        ]
      },
      {
        "q": "questions/Q2.png",
        "keys": [
          "HRX",
          "CVB",
          "IMP"
        ]
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 2": {
    "password": "bio101",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 3": {
    "password": "bio102",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 4": {
    "password": "bio103",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 5": {
    "password": "bio104",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "What is mitochondria?",
        "keys": [
          "Cell",
          "Ram",
          "Molecule"
        ]
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 6": {
    "password": "bio105",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "questions/Q2.png",
        "keys": [
          "HRX",
          "CVB",
          "IMP"
        ]
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 7": {
    "password": "bio106",
    "questions": [
      {
        "q": "questions/Q2.png",
        "keys": [
          "HRX",
          "CVB",
          "IMP"
        ]
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 8": {
    "password": "bio107",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      }
    ]
  },
  "Team 9": {
    "password": "bio108",
    "questions": [
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "",
        "keys": []
      },
      {
        "q": "What is mitochondria?",
        "keys": [
          "Cell",
          "Ram",
          "Molecule"
        ]
      }
    ]
  }
}
const API_BASE = window.location.protocol + '//' + window.location.host;
let currentTeam = null;
let currentQuestion = 0;
let serverMode = false; // true when logged in against the server
let teamPollId = null;

const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const huntContainer = document.getElementById("hunt-container");
const loginContainer = document.getElementById("login-container");
const teamTitle = document.getElementById("team-title");
const questionDisplay = document.getElementById("question-display");
const feedback = document.getElementById("feedback");
const answerForm = document.getElementById("answer-form");
const answerInput = document.getElementById("answer");

// ===== TEAM LOGIN =====
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const teamName = document.getElementById("teamName").value.trim();
  const password = document.getElementById("password").value.trim();

  // Try server-side login first (supports admin login). Fall back to local data if server unreachable.
    try {
    const res = await fetch(API_BASE + '/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team: teamName, password: password })
    });
    const data = await res.json();
    if (data && data.status === 'admin') {
      // admin authenticated — go to admin panel
      window.location.href = API_BASE + '/admin.html';
      return;
    }
    if (data && data.status === 'eliminated') {
      // team eliminated — redirect to eliminated page
      window.location.href = API_BASE + '/eliminated.html';
      return;
    }
    if (data && data.status === 'ok') {
      // team login accepted by server — proceed with local UI (questions still come from JS file)
      currentTeam = teamName;
      serverMode = true;
      loginContainer.classList.add("hidden");
      huntContainer.classList.remove("hidden");
      showQuestion();
      // start polling server for team state (elimination) every 2s
      if (!teamPollId) teamPollId = setInterval(async () => {
        try {
          const r = await fetch(`${API_BASE}/teams?cache=${Date.now()}`);
          if (!r.ok) return;
          const all = await r.json();
          const info = all && all[currentTeam];
          if (info && info.eliminated) {
            // redirect to eliminated page
            window.location.href = API_BASE + '/eliminated.html';
          }
        } catch (e) {
          // ignore transient errors
        }
      }, 2000);
      return;
    }
    // otherwise fall through to local check
  } catch (err) {
    // server unreachable — try local fallback below
    console.warn('Server login failed, falling back to local teams list', err);
  }

  // Local fallback (offline mode)
  if (teams[teamName] && teams[teamName].password === password) {
    currentTeam = teamName;
    loginContainer.classList.add("hidden");
    huntContainer.classList.remove("hidden");
    showQuestion();
  } else {
    loginError.textContent = "❌ Invalid team name or password!";
  }
});

function showQuestion() {
    const qData = teams[currentTeam].questions[currentQuestion];
    const qDisplay = document.getElementById("question-display");

    // Update team title
    teamTitle.textContent = `${currentTeam}, Question ${currentQuestion + 1}`;

        // Clear previous question
        qDisplay.innerHTML = "";
        // Determine type: prefer explicit qData.type, otherwise infer from extension
        let type = (qData.type || '').toString().toLowerCase();
        const src = qData.q || '';
        if (!type) {
            if (src.match(/\.(mp4|webm|ogg)$/i)) type = 'video';
            else if (src.match(/\.(gif)$/i)) type = 'gif';
            else if (src.match(/\.(jpg|jpeg|png|bmp|svg)$/i)) type = 'image';
            else type = 'text';
        }

        if (type === 'image' || type === 'gif') {
            const img = document.createElement('img');
            img.src = src;
            img.alt = `Question ${currentQuestion + 1}`;
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
            qDisplay.appendChild(img);
        } else if (type === 'video') {
            const video = document.createElement('video');
            video.src = src;
            video.controls = true;
            video.preload = 'metadata';
            video.style.maxWidth = '100%';
            video.style.height = 'auto';
            video.innerHTML = 'Your browser does not support the video tag.';
            qDisplay.appendChild(video);
        } else {
            const p = document.createElement('p');
            p.textContent = qData.q || '';
            qDisplay.appendChild(p);
        }

    // Reset input and feedback
    answerInput.value = "";
    feedback.textContent = "";

    // Apply fade-in animation
    qDisplay.classList.remove("fade-in"); // reset animation
    void qDisplay.offsetWidth; // trigger reflow
    qDisplay.classList.add("fade-in");
}

answerForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const qData = teams[currentTeam].questions[currentQuestion];
    const answer = answerInput.value.trim().toLowerCase();
    const validKeys = qData.keys.map(k => k.toLowerCase());

    if (validKeys.includes(answer)) {
        feedback.textContent = "✅ Correct!";
    // send answer to server if in serverMode
    const answeredQuestion = currentQuestion + 1;
    (async () => {
      if (serverMode && currentTeam) {
        try {
          const res = await fetch(`${API_BASE}/submit_answer`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ team: currentTeam, question: answeredQuestion, answer: answer, correct: true })
          });
          if (res.status === 403) {
            // eliminated
            window.location.href = API_BASE + '/eliminated.html';
            return;
          }
        } catch (e) {
          console.warn('Failed to POST answer to server', e);
        }
        // update question on server
        try {
          await fetch(`${API_BASE}/update_question`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ team: currentTeam, question: answeredQuestion + 1 })
          });
        } catch (e) {
          console.warn('Failed to update question on server', e);
        }
      }

      currentQuestion++;
      if (currentQuestion < teams[currentTeam].questions.length) {
        showQuestion();
      } else {
        questionDisplay.innerHTML = "<p>🎉 You’ve completed all your questions!</p>";
        answerForm.style.display = "none";
      }
    })();
    } else {
        feedback.textContent = "❌ Wrong key. Try again!";
    }
});
