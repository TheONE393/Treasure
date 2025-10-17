<?php
header('Content-Type: application/json');
$answersDir = __DIR__ . DIRECTORY_SEPARATOR . 'answers';
if (!is_dir($answersDir)) {
    // no answers yet
    echo json_encode(new stdClass());
    exit;
}

// If team parameter provided, return that team's answers
$team = $_GET['team'] ?? '';
if ($team) {
    $safe = preg_replace('/[^A-Za-z0-9_\-]/', '_', $team);
    $file = $answersDir . DIRECTORY_SEPARATOR . $safe . '.json';
    if (!file_exists($file)) {
        echo json_encode([]);
        exit;
    }
    $data = json_decode(file_get_contents($file), true);
    echo json_encode($data ?? []);
    exit;
}

// otherwise return all teams' answers as an object
$out = [];
$files = glob($answersDir . DIRECTORY_SEPARATOR . '*.json');
foreach ($files as $f) {
    $name = basename($f, '.json');
    $out[$name] = json_decode(file_get_contents($f), true) ?: [];
}

echo json_encode($out);
