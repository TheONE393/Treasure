This directory stores per-team answer logs in JSON format.

Each file is named <TeamNameSanitized>.json where non-alphanumeric characters are replaced with underscores.

Each entry is an object:
{
  "time": 163... ,  // unix timestamp
  "question": 1,
  "answer": "user typed answer",
  "correct": true/false
}

Admins can view these via admin panel's "View answers" button which fetches answers.php?team=<Team Name>.
