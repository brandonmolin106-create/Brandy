# Brandy — Echoes in the Dark studio repo

## ACE Studio (music / vocal synthesis)

ACE Studio is installed on Brandon's Windows machine. Its agent tooling only
works when the agent runs on **the same machine** as ACE Studio, with the app
open. Cloud sessions cannot reach it; in a cloud session, hand the ACE Studio
step to the user or to a local Cowork / Claude Code session.

Tool paths (Windows):

- CLI: `C:/Program Files/ACE Studio/acestudio-cli.exe`
- MCP server (stdio): `C:/Program Files/ACE Studio/ace-mcp-server.exe`

Prefer the CLI first. Run it with `help` to discover commands; mechanics
(arguments, enums, examples) live in the CLI's `help` and `get_docs`, not in
the skills. If the CLI is blocked by sandboxing or permissions, use the MCP
server instead. It is registered for this project in `.mcp.json` under the
name `ace-studio`; the user-scope registration command is:

```
claude mcp add --scope user ace-studio -- "C:\Program Files\ACE Studio\ace-mcp-server.exe"
```

Know-how for operating ACE Studio (features, workflow order, audio plugins,
setup) lives in `.claude/skills/ace-studio-*`. Those folders are a snapshot of
the official plugin at https://github.com/BeatMagic/acestudio_agent_plugin and
do not auto-update; the plugin install (`/plugin marketplace add
BeatMagic/acestudio_agent_plugin` then `/plugin install acestudio@acestudio`)
is the preferred route on a local machine. Docs:
https://docs.acestudio.ai/ai-agent/external-agent-access

## Repo layout

- `tmnt-story-mode/` — NeoForge Minecraft mod source (TMNT Turtle Power story mode).
- `download/` — built mod jar, world zip, modpack bundles and the one-file Windows installer.
- `installer/` — PowerShell installer script and the Python script that builds the `.bat`.
