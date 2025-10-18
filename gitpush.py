#!/usr/bin/env python3
"""gitpush.py - stage, commit, and push changes to the current git repo.

Usage:
  python gitpush.py -m "commit message"
  python gitpush.py --message "commit message"
  python gitpush.py --dry-run

This script will:
 - run `git add -A`
 - create a commit with the provided message (or a generated one)
 - push to the tracked remote branch (usually origin/<branch>)

It intentionally avoids interactive prompts and raises on errors.
"""
import argparse
import subprocess
import sys
import os
from datetime import datetime


def run(cmd, check=True, capture=False):
	if capture:
		return subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	else:
		return subprocess.run(cmd, shell=True, check=check)


def get_current_branch():
	r = run('git rev-parse --abbrev-ref HEAD', capture=True)
	if r.returncode != 0:
		raise SystemExit('Failed to determine current branch')
	return r.stdout.strip()


def main():
	parser = argparse.ArgumentParser(description='Stage, commit and push current repo')
	parser.add_argument('-m', '--message', help='Commit message. If omitted a timestamped message is used.')
	parser.add_argument('--dry-run', action='store_true', help="Show what would be done but don't run git commands")
	parser.add_argument('--remote', default='origin', help='Remote name to push to (default: origin)')
	args = parser.parse_args()

	if not os.path.isdir('.git') and not subprocess.run('git rev-parse --git-dir', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
		print('Not a git repository (no .git directory).')
		sys.exit(1)

	branch = get_current_branch()
	msg = args.message or f'Update: {datetime.utcnow().isoformat()}Z'

	print('Current branch:', branch)
	print('Remote:', args.remote)
	print('Commit message:', msg)

	if args.dry_run:
		print('\nDRY RUN: would run:')
		print('  git add -A')
		print(f'  git commit -m "{msg}"')
		print(f'  git push {args.remote} {branch}')
		return

	try:
		print('\nStaging changes...')
		run('git add -A')

		# Check if there is anything to commit
		status = run('git status --porcelain', capture=True)
		if status.stdout.strip() == '':
			print('No changes to commit.')
		else:
			print('Committing...')
			run(f'git commit -m "{msg}"')

		print('Pushing to remote...')
		run(f'git push {args.remote} {branch}')
		print('Push complete.')
	except subprocess.CalledProcessError as e:
		print('Git command failed:', e)
		sys.exit(1)


if __name__ == '__main__':
	main()

