# 🎯 Telegram Auto Reaction Bot (with Clone System)

Production-ready Telegram bot jo channels/groups ke messages par automatically emoji reactions lagata hai. Pyrogram v2 + MongoDB + unlimited clone bots support karta hai.

---

## 📐 Architecture

- **Engine:** Pyrogram v2 (`Client.send_reaction()` — native Bot API `setMessageReaction`)
- **Why Bot API reactions (not userbot)?** Safer, ToS-compliant, no session/account ban risk. Bot ko sirf group me **admin** banana hoga.
- **Database:** MongoDB (Motor async driver) — sab data permanent, restart-safe.
- **Clone Isolation:** Har clone ka data `clone_id` (= bot's own Telegram user ID) se prefix hota hai composite keys (`{clone_id}_{chat_id}`) me, isliye ek hi MongoDB cluster me sab clones ka data safely alag rehta hai.
- **Clone Runtime:** Master bot process ke andar hi har clone ek independent `pyrogram.Client` asyncio task ke roop me chalta hai — sabka apna token, apna in-memory session.

```
                    ┌─────────────────────┐
                    │     Master Bot       │  <-- Admin Panel (owner only)
                    │  /addclone /stats     │
                    └──────────┬───────────┘
                               │ spawns
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
            Clone Bot 1   Clone Bot 2   Clone Bot N
           (own token)   (own token)   (own token)
                 │             │             │
                 └──────┬──────┴──────┬──────┘
                        ▼             ▼
                     MongoDB (shared cluster,
                     data isolated by clone_id)
```

---

## 📂 Folder Structure

```
telegram-reaction-bot/
├── main.py                  # Entry point - starts master bot + resumes clones
├── config.py                 # Env-based configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── database/
│   ├── mongo.py               # Motor connection singleton
│   ├── clone_db.py            # Clone metadata CRUD
│   └── reaction_db.py         # Chat settings, users, stats CRUD
├── clone/
│   └── clone_manager.py       # Spawns/stops/restarts clone Client instances
├── plugins/                   # Auto-loaded by Pyrogram on every client (master + clones)
│   ├── start.py               # /start /help
│   ├── auto_react.py          # Core reaction engine (runs on every message)
│   ├── reaction_settings.py   # /setreaction /setdelay /togglereact /multireact
│   ├── admin.py                # /addclone /listclones /removeclone /clonestats
│   └── clone_commands.py       # /broadcast
└── utils/
    ├── logger.py               # Rotating file + console logging
    └── rate_limiter.py         # Sliding-window flood protection
```

---

## 🗄️ MongoDB Schema

**`clones`** — one doc per clone bot
```
_id: bot_id, bot_token, bot_username, api_id, api_hash,
owner_id, status (running/stopped), created_at,
default_delay, default_emojis
```

**`chat_settings`** — one doc per (clone, chat) pair
```
_id: "{clone_id}_{chat_id}", clone_id, chat_id, chat_title,
enabled, emojis[], delay, multi_reaction, added_at
```

**`users`** — one doc per (clone, user) — for broadcast
```
_id: "{clone_id}_{user_id}", clone_id, user_id, joined_at
```

**`stats`** — daily reaction counters
```
_id: "{clone_id}_{chat_id}_{yyyy-mm-dd}", reactions_sent
```

---

## 🤖 Commands

**Chat admins (inside any group/channel):**
| Command | Description |
|---|---|
| `/setreaction 👍 ❤️ 🔥` | Reaction emoji pool set karo |
| `/setdelay 5` | 0-60 sec ka reaction delay |
| `/togglereact` | Chat me reaction on/off |
| `/multireact on\|off` | Ek message par multiple emoji |
| `/mysettings` | Current chat settings dekho |
| `/allowedemojis` | Telegram-allowed emoji list |

**Bot owner (private chat, master or clone):**
| Command | Description |
|---|---|
| `/addclone <token>` | Naya clone bot banao (unlimited) |
| `/listclones` | Sab clones + status |
| `/stopclone <bot_id>` | Clone temporarily rok do |
| `/removeclone <bot_id>` | Clone permanently delete |
| `/clonestats <bot_id>` | Ek clone ka detailed stats |
| `/stats` | Global stats (master only) |
| `/broadcast` (reply to a msg) | Sab users ko forward karo |

---

## 🚀 Deployment Guide

### 1. Prerequisites
- Python 3.11+
- MongoDB (Atlas free tier ya self-hosted)
- Telegram `API_ID` / `API_HASH` — https://my.telegram.org
- Master `BOT_TOKEN` — @BotFather se

### 2. Local Setup
```bash
git clone <your-repo>
cd telegram-reaction-bot
cp .env.example .env
# .env me apni values fill karo
pip install -r requirements.txt
python main.py
```

### 3. Docker Setup (recommended for production)
```bash
cp .env.example .env
# .env me MONGO_URI ko "mongodb://mongo:27017" karo (docker-compose service name)
docker compose up -d --build
docker compose logs -f reaction-bot
```

### 4. VPS (systemd) Setup
```ini
# /etc/systemd/system/reaction-bot.service
[Unit]
Description=Telegram Reaction Bot
After=network.target

[Service]
WorkingDirectory=/opt/telegram-reaction-bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/telegram-reaction-bot/.env

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now reaction-bot
```

### 5. Adding your bot to a chat
1. Master bot ko private me `/addclone <token>` bhejo (agar clone chahiye) — warna master bot khud reaction bot hai.
2. Us bot ko target group/channel me **admin** banao (kam se kam "Post/Manage" permission).
3. Group me `/setreaction 👍 🔥 ❤️` bhejo — done, ab har naye message par reaction lagega.

---

## ⚠️ Important Notes

- Telegram sirf specific emoji set ko hi "reaction" ke roop me allow karta hai — poori list `/allowedemojis` se milegi. Custom/premium emoji reactions extra Bot API permissions maangte hain.
- Channels me reaction ke liye bot ko **admin with post permission** chahiye; discussion-group-linked channels me linked group me bhi admin hona better hai.
- Rate limiter (`utils/rate_limiter.py`) per-clone 20 reactions/minute tak limit karta hai by default — `Config.MAX_REACTIONS_PER_MINUTE` se adjust karo agar zyada high-traffic chats hain.
- Production me `in_memory=True` sessions restart pe naye login karte hain — agar aap chahte ho sessions persist ho, `workdir="sessions"` set karo Client me aur volume mount karo (Dockerfile me already volume diya hai).
