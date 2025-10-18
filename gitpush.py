#!/usr/bin/env python3
"""
gitpush.py

Run this script from the repository root to stage all changes, commit with a
timestamp (or a provided message), and push the current branch to origin.

Usage:
  python gitpush.py               # commit message will be current timestamp
  python gitpush.py "my message"  # use custom commit message

This script prints git output and returns non-zero on fatal errors.
"""
import subprocess
import sys
import datetime
import os


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip())
    return res


def main():
    # Ensure we run git commands from the script's containing directory so the
    # script can be moved into other repos without breaking (avoids nested gitlink issues).
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_dir)

    # check we are in a git repo
    res = run(["git", "rev-parse", "--is-inside-work-tree"])
    if res.returncode != 0:
        print("Not a git repository (or git not installed). Aborting.")
        return 2

    # find current branch
    res = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if res.returncode != 0:
        print("Failed to determine current branch. Aborting.")
        return 3
    branch = res.stdout.strip()
    print(f"Current branch: {branch}")

    # stage all changes (respecting .gitignore)
    res = run(["git", "add", "--all"])
    if res.returncode != 0:
        print("git add failed. Aborting.")
        return 4

    # commit with timestamp or provided message
    if len(sys.argv) > 1:
        msg = sys.argv[1]
    else:
        msg = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    res = run(["git", "commit", "-m", msg])
    if res.returncode != 0:
        out = (res.stdout or "") + (res.stderr or "")
        lowered = out.lower()
        if "nothing to commit" in lowered or "no changes added to commit" in lowered:
            print("Nothing to commit. Skipping commit step.")
        else:
            print("git commit failed. Aborting.")
            return 5

    # push to origin (allow disabling push via env var GITPUSH_DRY_RUN=1)
    if os.environ.get('GITPUSH_DRY_RUN'):
        print("GITPUSH_DRY_RUN set — skipping actual git push.")
    else:
        res = run(["git", "push", "-u", "origin", branch])
        if res.returncode != 0:
            # detect nested repo warning in stderr/stdout and print guidance
            out = (res.stdout or "") + (res.stderr or "")
            if 'adding embedded git repository' in out.lower() or 'submodule' in out.lower():
                print("Warning: repository contains nested git data (gitlink). If you moved this folder into another git repo, consider removing embedded .git directories or using .gitmodules if intended.")
            print("git push failed.")
            return 6
    if res.returncode != 0:
        print("git push failed.")
        return 6

    print("Push complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
