# Security Policy

## Supported versions

This is a personal project, so realistically only the latest `main` is supported. If you
are running something older, pull the latest first.

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | yes                |
| < 0.2   | no                 |

## Reporting a vulnerability

Please do not open a public issue for security problems. Instead email
danny.zweben99@gmail.com with:

- what the issue is
- how to reproduce it
- how bad you think it is

I will try to respond within a few days. Since this is a hobby project there is no bug
bounty, but you will get a genuine thank you and credit if you want it.

## A few notes on the design

- API keys live in `.env`, which is gitignored. Never commit real keys.
- The `python_repl` tool is sandboxed with a blocklist, not a real jail. Do not expose the
  agent to untrusted input on a machine you care about.
- The `http_get` / `fetch_url` tools will fetch arbitrary URLs the model picks, so run the
  agent somewhere you are comfortable making outbound requests from.
