# Security Policy

## Scope

This repository contains research, architecture, backtesting and validation code. It is provided for research only.

## Reporting a vulnerability

Please report security problems privately, not in a public issue or pull request:

1. Open this repository's **Security** tab and choose **Report a vulnerability** (GitHub private vulnerability reporting).
2. Describe the problem, the affected file(s) and the steps to reproduce it.
3. You should receive an acknowledgement within 7 days. Please allow time for a fix before any public disclosure.

## Never post secrets

- Do not include API keys, tokens, passwords, account numbers or personal data in issues, pull requests, discussions or reports.
- If you find a secret committed in this repository, report only its location (file and line). Do not copy the value.
- Configuration belongs in a local `.env` file, which is git-ignored. Use `.env.example` for variable names only.

## Supported versions

Only the latest commit on `main` is supported.
