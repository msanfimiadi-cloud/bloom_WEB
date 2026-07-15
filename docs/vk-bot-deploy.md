# Bloom Club VK bot deploy

VK Mini App is not required: the bot only gives a Browser App login code and a link to `https://app.bloomclub.ru`.

## VK setup

1. Create or open a VK community.
2. In community settings, enable **Messages**.
3. In **API usage**, create a community access token with permission to manage community messages.
4. Enable **Bots Long Poll API**.
5. Enable the `message_new` event.
6. Copy the numeric community ID from the community page or API settings; use it as `VK_GROUP_ID`.

## Environment

Add these variables to the production `.env` used by systemd:

```dotenv
VK_BOT_TOKEN=...
VK_GROUP_ID=...
VK_API_VERSION=5.199
VK_LONGPOLL_WAIT=25
VK_LONGPOLL_MODE=2
VK_LONGPOLL_VERSION=3
INTERNAL_API_BASE_URL=http://127.0.0.1:8000
INTERNAL_API_KEY=...
BROWSER_APP_URL=https://app.bloomclub.ru
```

`INTERNAL_API_KEY` must match the backend internal bot service token (`BOT_SERVICE_TOKEN`). Do not put secrets in logs or commit them.

## Install systemd service

```bash
sudo cp deploy/systemd/bloomclub-vk-bot.service /etc/systemd/system/bloomclub-vk-bot.service
sudo systemctl daemon-reload
sudo systemctl enable bloomclub-vk-bot.service
sudo systemctl start bloomclub-vk-bot.service
```

## Operations

```bash
sudo systemctl status bloomclub-vk-bot.service
sudo journalctl -u bloomclub-vk-bot.service -f
sudo systemctl restart bloomclub-vk-bot.service
sudo systemctl stop bloomclub-vk-bot.service
```

The bot runs separately from `womenclub.service` and calls `POST /api/v1/internal/login-code` with provider `vk`.
