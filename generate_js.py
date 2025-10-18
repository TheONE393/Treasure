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

# ==== EXPORT ONLY JSON ====
def build_json(teams_dict):
    return json.dumps(teams_dict, indent=2)

# ==== MAIN ====
def main():
    question_bank = load_questions(questions_folder)
    if not question_bank:
        print("⚠️ No questions found!")
        return

    teams_dict = load_team_data(csv_file, question_bank)

    # ---- EXPORT JSON ----
    with open(output_json, "w", encoding="utf-8") as f:
        f.write(build_json(teams_dict))
    print(f"✅ teams.json generated successfully!")

if __name__ == "__main__":
    main()
