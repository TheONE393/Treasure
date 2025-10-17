<?php
header('Content-Type: application/json');

$teamsFile = 'teams.json';

// Load teams data
if (!file_exists($teamsFile)) {
    $teamsData = [];
    file_put_contents($teamsFile, json_encode($teamsData, JSON_PRETTY_PRINT));
} else {
    $teamsData = json_decode(file_get_contents($teamsFile), true);
}

// === POST actions ===
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'add_time') {
        $team = $_POST['team'] ?? '';
        $minutes = intval($_POST['minutes'] ?? 0);

        if ($team && isset($teamsData[$team])) {
            if (!isset($teamsData[$team]['extraTime'])) $teamsData[$team]['extraTime'] = 0;
            $teamsData[$team]['extraTime'] += $minutes * 60;
            file_put_contents($teamsFile, json_encode($teamsData, JSON_PRETTY_PRINT));
            echo json_encode(['status'=>'ok']);
            exit;
        }
    } elseif ($action === 'update_question') {
        $team = $_POST['team'] ?? '';
        $question = intval($_POST['question'] ?? 1);
        if ($team && isset($teamsData[$team])) {
            $teamsData[$team]['currentQuestion'] = $question;
            file_put_contents($teamsFile, json_encode($teamsData, JSON_PRETTY_PRINT));
            echo json_encode(['status'=>'ok']);
            exit;
        }
    } elseif ($action === 'submit_answer') {
        // Log each answer attempt to answers/<sanitized_team>.json
        $team = $_POST['team'] ?? '';
        $question = intval($_POST['question'] ?? 0);
        $answer = $_POST['answer'] ?? '';
        $correct = isset($_POST['correct']) && ($_POST['correct'] == '1' || $_POST['correct'] === 'true');

        if ($team) {
            $answersDir = __DIR__ . DIRECTORY_SEPARATOR . 'answers';
            if (!is_dir($answersDir)) mkdir($answersDir, 0755, true);
            // sanitize filename
            $safe = preg_replace('/[^A-Za-z0-9_\-]/', '_', $team);
            $file = $answersDir . DIRECTORY_SEPARATOR . $safe . '.json';

            $entry = [
                'time' => time(),
                'question' => $question,
                'answer' => $answer,
                'correct' => $correct
            ];

            $existing = [];
            if (file_exists($file)) {
                $existing = json_decode(file_get_contents($file), true) ?: [];
            }
            $existing[] = $entry;
            file_put_contents($file, json_encode($existing, JSON_PRETTY_PRINT));
            echo json_encode(['status' => 'ok']);
            exit;
        }
    }
    echo json_encode(['status'=>'error']);
    exit;
}

// === GET: return team data ===
// normalize teams to ensure admin has fields
foreach ($teamsData as $t => &$info) {
    if (!isset($info['currentQuestion']) || !$info['currentQuestion']) $info['currentQuestion'] = 1;
    if (!isset($info['extraTime'])) $info['extraTime'] = 0;
    // loginTime may be absent until they actually log in
}
unset($info);

echo json_encode($teamsData);
