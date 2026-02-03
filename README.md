# elevenlabs-skill

🔊 Text-to-speech, sound effects, music generation, voice management, and quota checks via the [ElevenLabs](https://elevenlabs.io) API.

An [OpenClaw](https://openclaw.ai) skill.

## Quick Start

```bash
# Requires ELEVENLABS_API_KEY
python3 scripts/speech.py "Hello world" -v <voice_id> -o hello.mp3
python3 scripts/sfx.py "Cinematic boom" -o boom.mp3
python3 scripts/music.py --prompt "Jazz piano" --length-ms 10000 -o jazz.mp3
python3 scripts/voices.py
python3 scripts/quota.py
```

See [SKILL.md](SKILL.md) for full documentation.

## Links

- **GitHub**: https://github.com/odrobnik/elevenlabs-skill
- **ClawHub**: https://www.clawhub.com/skills/elevenlabs
