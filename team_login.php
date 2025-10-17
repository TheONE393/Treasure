<?php
$teamsFile='teams.json';
$teamsData = file_exists($teamsFile) ? json_decode(file_get_contents($teamsFile), true) : [];

$team = $_POST['team'] ?? '';
$password = $_POST['password'] ?? '';

if ($_SERVER['REQUEST_METHOD']==='POST') {
    if(isset($teamsData[$team]) && $teamsData[$team]['password']===$password){
        $teamsData[$team]['loginTime'] = time();
        file_put_contents($teamsFile, json_encode($teamsData, JSON_PRETTY_PRINT));
        echo "Login successful";
        exit;
    } else {
        echo "Invalid team or password";
        exit;
    }
}
?>

<form method="post">
    Team: <input name="team" required><br>
    Password: <input name="password" type="password" required><br>
    <button type="submit">Login</button>
</form>
