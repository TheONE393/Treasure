import os
import csv
import json

# ==== CONFIGURATION ====
csv_file = "team_questions.csv"      # CSV file with team-question mapping
questions_folder = "questions"       # Folder with Question 1.txt or Q1.png
output_js = "script.js"              # Output JavaScript file
output_json = "teams.json"           # JSON file for admin or backup

# ==== LOAD QUESTIONS ====
def load_questions(folder):
    question_data = {}
    files = os.listdir(folder)
    for file in files:
        file_lower = file.lower()

        # extract question number
        if file_lower.startswith("q") or file_lower.startswith("question"):
            num_part = ''.join(filter(str.isdigit, file))
            if not num_part:
                continue
            q_num = int(num_part)
            path = os.path.join(folder, file).replace("\\","/")

            # IMAGE or GIF or VIDEO QUESTION
            if file_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")):
                qtype = 'gif' if file_lower.endswith('.gif') else 'image'
                if q_num not in question_data:
                    question_data[q_num] = {"q": path, "keys": [], "type": qtype}
                else:
                    question_data[q_num]["q"] = path  # replace q if previously text
                    question_data[q_num]["type"] = qtype

            # VIDEO QUESTION
            elif file_lower.endswith((".mp4", ".webm", ".ogg")):
                qtype = 'video'
                if q_num not in question_data:
                    question_data[q_num] = {"q": path, "keys": [], "type": qtype}
                else:
                    question_data[q_num]["q"] = path
                    question_data[q_num]["type"] = qtype

            # TEXT FILE
            elif file_lower.endswith(".txt"):
                # read keys and optionally text
                with open(path, "r", encoding="utf-8") as f:
                    keys = []
                    q_text = None
                    for line in f:
                        if line.lower().startswith("question:"):
                            q_text = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("keys:"):
                            keys = [k.strip() for k in line.split(":", 1)[1].split(",")]
                    if q_num not in question_data:
                        # no media exists, use text
                        if q_text:
                            question_data[q_num] = {"q": q_text, "keys": keys, "type": 'text'}
                        else:
                            question_data[q_num] = {"q": "", "keys": keys, "type": 'text'}
                    else:
                        # media exists, just update keys (keep existing type)
                        question_data[q_num]["keys"] = keys
    return question_data

# ==== LOAD TEAM DATA ====
def load_team_data(csv_file, question_bank):
    teams = {}
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            team = row["Team"].strip()
            q_numbers = [
                int(row[f"Q{i}"]) for i in range(1, 5)
                if row.get(f"Q{i}") and row[f"Q{i}"].strip().isdigit()
            ]

            if team not in teams:
                # Auto-generate password
                teams[team] = {
                    "password": f"bio{100 + len(teams)}",
                    "questions": []
                }

            teams[team]["questions"] = [
                {
                    "q": question_bank[q]["q"],
                    "keys": question_bank[q]["keys"]
                }
                for q in q_numbers if q in question_bank
            ]

    return teams

# ==== BUILD JS ====
def build_js(teams_dict):
    js_header = "// Auto-generated Treasure Hunt script (text + image questions)\nconst teams = "
    js_content = json.dumps(teams_dict, indent=2)
    js_footer = """
let currentTeam = null;
let currentQuestion = 0;

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
loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const teamName = document.getElementById("teamName").value.trim();
    const password = document.getElementById("password").value.trim();

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
        currentQuestion++;
        if (currentQuestion < teams[currentTeam].questions.length) {
            showQuestion();
        } else {
            questionDisplay.innerHTML = "<p>🎉 You’ve completed all your questions!</p>";
            answerForm.style.display = "none";
        }
    } else {
        feedback.textContent = "❌ Wrong key. Try again!";
    }
});
"""
    return js_header + js_content + js_footer

# ==== MAIN ====
def main():
    question_bank = load_questions(questions_folder)
    if not question_bank:
        print("⚠️ No questions found!")
        return

    teams_dict = load_team_data(csv_file, question_bank)

    # ---- EXPORT JS ----
    js_code = build_js(teams_dict)
    with open(output_js, "w", encoding="utf-8") as f:
        f.write(js_code)
    print("✅ script.js generated successfully!")

    # ---- EXPORT JSON ----
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(teams_dict, f, indent=2)
    print(f"✅ teams.json generated successfully!")

if __name__ == "__main__":
    main()
