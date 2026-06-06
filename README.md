# Undercover Discord Bot

A simple Discord bot to run **Undercover** games with a slash command.

The bot lets you:

- start a game with `/undercover`
- optionally choose a word category
- configure the number of **Undercovers** and **Mr. Whites**
- select the players from an interactive Discord menu
- automatically send each player their role and word by DM

## Requirements

- Python 3.10+
- A Discord bot application
- `MESSAGE CONTENT` intent is **not** required
- `SERVER MEMBERS INTENT` must be enabled for the bot

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your bot token in an environment variable:

```bash
set DISCORD_TOKEN=your_token_here
```

4. Start the bot:

```bash
python bot.py
```

## Docker

Build the image:

```bash
docker build -f DOCKERFILE -t undercover-bot .
```

Run the container:

```bash
docker run --rm -e DISCORD_TOKEN=your_token_here -v "${PWD}/words:/app/words" undercover-bot
```

## Discord bot setup

In the [Discord Developer Portal](https://discord.com/developers/applications):

1. Create an application and a bot.
2. Copy the bot token.
3. Enable **Server Members Intent** in the bot settings.
4. Invite the bot to your server with the `applications.commands` and `bot` scopes.

## Word categories

The bot loads categories from JSON files inside the `words` folder.

If the folder does not exist, the bot creates it automatically on startup.

Each JSON file becomes one category.  
For example, `animals.json` creates the `animals` category.

### File format

Each file must contain a non-empty JSON array of word pairs:

```json
[
  ["dog", "wolf"],
  ["cat", "tiger"],
  ["rabbit", "hare"]
]
```

For each game, the bot randomly picks **one** pair:

- civilians receive the first word
- undercovers receive the second word
- Mr. White receives no word

## Command usage

### `/undercover`

Starts the setup flow for a new Undercover game.

#### Parameters

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `undercovers` | integer | No | `1` | Number of Undercover players |
| `mr_whites` | integer | No | `0` | Number of Mr. White players |
| `category` | string | No | random | Word category to use |

## Example

```text
/undercover undercovers:2 mr_whites:1 category:animals
```