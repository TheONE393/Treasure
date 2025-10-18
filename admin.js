let teamsData = {};
// Use the page origin as the API base so the admin UI works when served by the Flask server
const API_BASE = window.location.protocol + '//' + window.location.host;
let dataSource = API_BASE + '/teams'; // indicates where data was loaded from
// keep track of which teams have their answers panel open so refreshes can re-open them
let openAnswerTeams = new Set();
// keep track of which teams have their action dropdown open so polling doesn't close them
let openDropdownTeams = new Set();
// cached answers for teams (so we can re-render immediately on table refresh)
let openAnswerData = {};

// Fetch live data (with basic error handling and JSON validation)
async function fetchTeams() {
    try {
        const response = await fetch(dataSource + "?cache=" + Date.now(), { cache: 'no-store', mode: 'cors' });
        if (!response.ok) {
            const msg = 'Network response was not ok: ' + response.status;
            console.error(msg);
            throw new Error(msg);
        }
        const text = await response.text();
        let data;
            try {
                data = JSON.parse(text);
                teamsData = data || {};
                renderTable();
                console.log('Fetched teams, count=', Object.keys(teamsData).length);
            } catch (e) {
                console.warn('Invalid JSON from API — response text:\n', text);
                console.warn('Invalid JSON from API, attempting fallback to teams.json');
            // try fallback to static teams.json (read-only)
            try {
                const resp2 = await fetch('teams.json?cache=' + Date.now());
                if (!resp2.ok) throw new Error('teams.json fetch failed');
                const txt2 = await resp2.text();
                const data2 = JSON.parse(txt2);
                dataSource = 'teams.json';
                teamsData = data2 || {};
                renderTable();
                return;
            } catch (e2) {
                console.error('Fallback to teams.json failed', e2);
                const tbody = document.getElementById('team-table');
                tbody.innerHTML = '<tr><td colspan="4">Invalid data from server</td></tr>';
                return;
            }
        }
    } catch (e) {
        console.error("Error fetching teams", e);
        const tbody = document.getElementById('team-table');
        if (tbody) tbody.innerHTML = '<tr><td colspan="4">Error loading teams</td></tr>';
    }
}

function renderTable() {
    const tbody = document.getElementById("team-table");
    if (!tbody) return;
    tbody.innerHTML = "";

    const teamNames = Object.keys(teamsData || {});
    if (teamNames.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No teams available</td></tr>';
        return;
    }

    // Connect indicator
    const noteTr = document.createElement('tr');
    const noteTd = document.createElement('td');
    noteTd.colSpan = 4;
    noteTd.style.background = '#4CAF50';
    noteTd.style.color = 'white';
    noteTd.style.fontSize = '0.9em';
    noteTd.textContent = '✓ Connected to server - Auto-updating every second';
    noteTr.appendChild(noteTd);
    tbody.appendChild(noteTr);

    teamNames.forEach(team => {
        const info = teamsData[team] || {};
        const tr = document.createElement("tr");

        // Team
    const tdName = document.createElement("td");
    tdName.textContent = team;
    tdName.setAttribute("data-label", "Team");
    // store canonical team name for reliable DOM lookups
    tdName.dataset.team = team;

        // Current Question (fallback to 1)
        const tdQ = document.createElement("td");
        const currentQ = (typeof info.currentQuestion !== 'undefined' && info.currentQuestion !== null) ? info.currentQuestion : 1;
        tdQ.textContent = currentQ;
        tdQ.setAttribute("data-label", "Current Question");

        // Time Spent
        const tdTime = document.createElement("td");
        tdTime.setAttribute("data-label", "Time Spent");
        if (info.loginTime) {
            const spent = Math.floor(Date.now()/1000) - Number(info.loginTime);
            tdTime.textContent = formatTime(spent);
        } else {
            tdTime.textContent = "Not logged in";
        }

    // Actions
    const tdActions = document.createElement("td");
    tdActions.setAttribute("data-label", "Actions");
    tdActions.classList.add('actions');

        // Eliminate time button (replaces Reset) — permanently marks eliminated for this server session
        const eliminateBtn = document.createElement('button');
        eliminateBtn.textContent = '�️ Eliminate';
        eliminateBtn.classList.add('action-btn','danger');
        eliminateBtn.addEventListener('click', async () => {
            if (!confirm(`Permanently eliminate time for ${team} for the current server session? This cannot be undone until the server is restarted.`)) return;
            try {
                const res = await fetch(API_BASE + '/eliminate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ team: team })
                });
                if (!res.ok) throw new Error('Failed to eliminate time');
                fetchTeams(); // refresh the table
            } catch (e) {
                console.error('Eliminate failed:', e);
                alert('Failed to eliminate time. Please try again.');
            }
        });

        // If team is already eliminated for this server session, render a persistent badge and disable the button
        if (info && info.eliminated) {
            // create badge next to the team name (append later to the name cell)
            const badge = document.createElement('span');
            badge.textContent = 'Eliminated';
            badge.classList.add('eliminated-badge');
            badge.style.marginLeft = '8px';
            badge.style.color = '#fff';
            badge.style.background = '#d9534f';
            badge.style.padding = '2px 6px';
            badge.style.borderRadius = '4px';
            badge.style.fontSize = '0.8em';
            // disable the button and change its text so it doesn't flash during polls
            eliminateBtn.disabled = true;
            eliminateBtn.textContent = 'Eliminated';
            eliminateBtn.classList.add('disabled');
            // append badge to the team name cell later (we'll attach it after tdName is available)
            tdName && tdName.appendChild && tdName.appendChild(badge);
        }
        tdActions.appendChild(eliminateBtn);

        // Dropdown for extra admin actions (Skip / Pause)
        const dropdownWrap = document.createElement('div');
        dropdownWrap.classList.add('action-dropdown');
        const ddBtn = document.createElement('button');
        ddBtn.textContent = '⋮';
        ddBtn.classList.add('small-btn');
        ddBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('open');
            // persist open state across polling re-renders
            if (dropdownMenu.classList.contains('open')) openDropdownTeams.add(team);
            else openDropdownTeams.delete(team);
        });
        const dropdownMenu = document.createElement('div');
        dropdownMenu.classList.add('action-menu');

    const skipOpt = document.createElement('button');
        skipOpt.textContent = 'Skip question';
        skipOpt.classList.add('small-btn');
        skipOpt.addEventListener('click', async () => {
            if (!confirm(`Skip current question for ${team}?`)) return;
            try {
                const r = await fetch(API_BASE + '/skip_question', {
                    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({team: team})
                });
                if (!r.ok) throw new Error('skip failed');
                fetchTeams();
            } catch (e) { console.error(e); alert('Skip failed'); }
        });

    const pauseOpt = document.createElement('button');
        pauseOpt.textContent = info.pauseStart ? 'Resume timer' : 'Pause timer';
        pauseOpt.classList.add('small-btn');
        pauseOpt.addEventListener('click', async () => {
            try {
                const action = info.pauseStart ? 'resume' : 'pause';
                const r = await fetch(API_BASE + '/pause_timer', {
                    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({team: team, action: action})
                });
                if (!r.ok) throw new Error('pause failed');
                fetchTeams();
            } catch (e) { console.error(e); alert('Pause/Resume failed'); }
        });

        dropdownMenu.appendChild(skipOpt);
        dropdownMenu.appendChild(pauseOpt);
        dropdownWrap.appendChild(ddBtn);
        dropdownWrap.appendChild(dropdownMenu);
        tdActions.appendChild(dropdownWrap);

        // If this team's dropdown was open previously, restore its open state after render
        if (openDropdownTeams.has(team)) {
            dropdownMenu.classList.add('open');
        }

        // View answers button
    const viewBtn = document.createElement('button');
    viewBtn.textContent = 'View answers';
    viewBtn.classList.add('action-btn');
        viewBtn.addEventListener('click', () => {
            // toggle in-memory state and then open/close accordingly
            if (openAnswerTeams.has(team)) {
                openAnswerTeams.delete(team);
                delete openAnswerData[team];
                // remove any existing details row immediately
                const next = tr.nextSibling;
                if (next && next.classList && next.classList.contains('answers-row')) next.remove();
            } else {
                openAnswerTeams.add(team);
                // fetch answers, cache them, and insert immediately
                fetchAndCacheAnswers(team).then(data => {
                    try { insertAnswersRow(tr, data); } catch (e) { console.error(e); }
                }).catch(err => console.error('Failed to fetch answers', err));
            }
        });
        tdActions.appendChild(viewBtn);

        tr.appendChild(tdName);
        tr.appendChild(tdQ);
        tr.appendChild(tdTime);
        tr.appendChild(tdActions);
        tbody.appendChild(tr);

        // If this team's answers panel was previously opened, reopen it after inserting the row
        if (openAnswerTeams.has(team)) {
            // If we have cached answers render them synchronously; otherwise fetch then render
            if (openAnswerData[team]) {
                insertAnswersRow(tr, openAnswerData[team]);
            } else {
                fetchAndCacheAnswers(team).then(data => insertAnswersRow(tr, data)).catch(err => console.error('Failed to reopen answers for', team, err));
            }
        }
    });

    // After rendering the table, refresh any open answers panels so they show live updates
    openAnswerTeams.forEach(team => {
        // fetch and re-render answers for teams that have the answers panel open
        fetchAndCacheAnswers(team).then(data => {
            try {
                // find the row for this team and re-insert the answers row under it
                const rows = Array.from(document.querySelectorAll('#team-table tr'));
                for (let i = 0; i < rows.length; i++) {
                    const r = rows[i];
                    const nameCell = r.querySelector && r.querySelector('td[data-team]');
                    if (nameCell && nameCell.dataset && nameCell.dataset.team === team) {
                        insertAnswersRow(r, data);
                        break;
                    }
                }
            } catch (e) {
                console.error('Failed to refresh answers panel for', team, e);
            }
        }).catch(err => console.warn('Failed to refresh answers for', team, err));
    });
}

// Fetch a specific team's answers and display as a small details row under the team row
// fetch a specific team's answers and insert a details row under `row`.
// `forceOpen` when true will ensure the details row is inserted and not toggled closed.
// fetch answers from server and cache them for the team
async function fetchAndCacheAnswers(team) {
    const resp = await fetch(`${API_BASE}/answers?team=${encodeURIComponent(team)}&cache=${Date.now()}`);
    if (!resp.ok) throw new Error('Failed to fetch answers');
    const data = await resp.json();
    openAnswerData[team] = data || [];
    return openAnswerData[team];
}

// insert a details row with `data` under `row` (synchronous DOM op)
function insertAnswersRow(row, data) {
    // remove any existing details row first so we can replace it with fresh content
    const next = row.nextSibling;
    if (next && next.classList && next.classList.contains('answers-row')) {
        next.remove();
    }
    const detailsTr = document.createElement('tr');
    detailsTr.classList.add('answers-row');
    const td = document.createElement('td');
    td.colSpan = 4;

    if (!data || data.length === 0) {
        td.textContent = 'No answers yet';
    } else {
        const ul = document.createElement('ul');
        data.forEach(entry => {
            const li = document.createElement('li');
            const time = new Date(entry.time * 1000).toLocaleString();
            li.textContent = `${time} — Q${entry.question}: "${entry.answer}" ${entry.correct ? '(correct)' : ''}`;
            ul.appendChild(li);
        });
        td.appendChild(ul);
    }

    detailsTr.appendChild(td);
    row.parentNode.insertBefore(detailsTr, row.nextSibling);
}

// Update a team's current question on the server
// Format seconds
function formatTime(s){
    const h=Math.floor(s/3600);
    const m=Math.floor((s%3600)/60);
    const sec=s%60;
    return h + 'h ' + m + 'm ' + sec + 's';
}

// Start with an immediate fetch, then refresh every second (single interval)
fetchTeams();
let intervalId = setInterval(fetchTeams, 1000);

// Stop updates if page is hidden, and resume with a single interval when visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    } else {
        fetchTeams(); // immediate update when visible again
        if (!intervalId) intervalId = setInterval(fetchTeams, 1000);
    }
});

// Close dropdown menus when clicking outside a dropdown. Keep them open when clicking inside.
document.addEventListener('click', (e) => {
    // if the click happened inside any action-dropdown, do nothing
    if (e.target && e.target.closest && e.target.closest('.action-dropdown')) {
        return;
    }
    // otherwise close all and clear persisted state
    document.querySelectorAll('.action-menu.open, .action-menu.opened').forEach(el => el.classList.remove('open','opened'));
    openDropdownTeams.clear();
});
