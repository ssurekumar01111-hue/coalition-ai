# Groundswell: AI Coalition Agent (Bolt for Python and Pydantic)

Meet Groundswell — an AI-powered coalition agent that lives in Slack. Groundswell autonomously assembles donors, NGOs, volunteers, and grants around educational needs, forming mission-driven coalitions in minutes, all without leaving the conversation.

Built with [Bolt for Python](https://docs.slack.dev/tools/bolt-python/) and [Pydantic AI](https://ai.pydantic.dev/) using models from [Anthropic](https://anthropic.com), [Google](https://ai.google.dev/), or [OpenAI](https://openai.com).

## App Overview

Groundswell gives your team four ways to launch educational missions:

* **App Home** — Users open Groundswell's Home tab and choose from need categories (Laptops & Devices, Books & Literacy, STEM Workshops, Mentorship, Other). A modal collects details, then Groundswell posts a coalition summary in a dedicated mission channel.
* **Direct Messages** — Users message Groundswell directly to describe an educational need. Groundswell responds in-thread, maintaining context across follow-ups.
* **Channel @mentions** — Users mention `@Groundswell` in any channel to describe a need and receive a coalition in-thread.
* **Assistant Panel** — Users click _Add Agent_ in Slack, select Groundswell, and pick from suggested prompts or describe a need.

Groundswell uses the Coalition MCP Server to assemble resources in real time:

* **Donor Search** — Finds matching donors for the resource type and location.
* **NGO Partner Search** — Identifies NGO partners aligned with the mission focus area.
* **Volunteer Search** — Surfaces active volunteers with the required skills.
* **Grant Search** — Locates available grants by focus area and location.
* **Build Coalition** — Assembles all of the above into a scored, actionable coalition summary.

> **Note:** All MCP tools query a local data layer. In production, these would connect to your live donor/NGO/grant databases.

### Slack MCP Server

Groundswell also works with the [Slack MCP Server](https://docs.slack.dev/ai/slack-mcp-server), giving it the ability to search messages and files, read channel history and threads, send messages, schedule messages, and create or update Slack canvases. When deployed with OAuth (HTTP mode), Groundswell automatically connects to the Slack MCP Server using the user's token, unlocking these capabilities on top of the built-in coalition tools.

## Setup

Before getting started, make sure you have a development workspace where you have permissions to install apps.

### Developer Program

Join the [Slack Developer Program](https://api.slack.com/developer-program) for exclusive access to sandbox environments for building and testing your apps, tooling, and resources created to help you build and grow.

### Create the Slack app

<details><summary><strong>Using Slack CLI</strong></summary>

Install the latest version of the Slack CLI for your operating system:

- [Slack CLI for macOS & Linux](https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli-for-mac-and-linux/)
- [Slack CLI for Windows](https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli-for-windows/)

You'll also need to log in if this is your first time using the Slack CLI.

```sh
slack login
```

#### Initializing the project

```sh
slack create my-casey-agent --template slack-samples/bolt-python-support-agent --subdir pydantic-ai
cd my-casey-agent
```

</details>

<details><summary><strong>Using App Settings</strong></summary>

#### Create Your Slack App

1. Open [https://api.slack.com/apps/new](https://api.slack.com/apps/new) and choose "From an app manifest"
2. Choose the workspace you want to install the application to
3. Copy the contents of [manifest.json](./manifest.json) into the text box that says `*Paste your manifest code here*` (within the JSON tab) and click _Next_
4. Review the configuration and click _Create_
5. Click _Install to Workspace_ and _Allow_ on the screen that follows. You'll then be redirected to the App Configuration dashboard.

#### Environment Variables

Before you can run the app, you'll need to store some environment variables.

1. Rename `.env.sample` to `.env`.
2. Open your apps setting page from [this list](https://api.slack.com/apps), click _OAuth & Permissions_ in the left hand menu, then copy the _Bot User OAuth Token_ into your `.env` file under `SLACK_BOT_TOKEN`.

```sh
SLACK_BOT_TOKEN=YOUR_SLACK_BOT_TOKEN
```

3. Click _Basic Information_ from the left hand menu and follow the steps in the _App-Level Tokens_ section to create an app-level token with the `connections:write` scope. Copy that token into your `.env` as `SLACK_APP_TOKEN`.

```sh
SLACK_APP_TOKEN=YOUR_SLACK_APP_TOKEN
```

#### Initializing the project

```sh
git clone https://github.com/slack-samples/bolt-python-support-agent.git my-casey-agent
cd my-casey-agent
```

</details>

### Setup your python virtual environment

```sh
python3 -m venv .venv
source .venv/bin/activate  # for Windows OS, .\.venv\Scripts\Activate instead should work
```

#### Install dependencies

```sh
pip install -r requirements.txt
```

## Providers

This app supports both Anthropic and OpenAI as AI providers. Set at least one API key — if both are set, Anthropic is used by default.

### Anthropic Setup

Uses Anthropic's `claude-sonnet-4-6` model through Pydantic AI.

1. Create an API key from your [Anthropic dashboard](https://console.anthropic.com/settings/keys).
1. Rename `.env.sample` to `.env`.
3. Save the Anthropic API key to `.env`:

```sh
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY
```

### OpenAI Setup

Uses OpenAI's `gpt-4.1-mini` model through Pydantic AI.

1. Create an API key from your [OpenAI dashboard](https://platform.openai.com/api-keys).
1. Rename `.env.sample` to `.env`.
3. Save the OpenAI API key to `.env`:

```sh
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

## Development

### Starting the app

<details><summary><strong>Using the Slack CLI</strong></summary>

#### Slack CLI

```sh
slack run
```
</details>

<details><summary><strong>Using the Terminal</strong></summary>

#### Terminal

```sh
python3 app.py
```

</details>

<details><summary><strong>Using OAuth HTTP Server (with ngrok)</strong></summary>

#### OAuth HTTP Server

This mode uses an HTTP server instead of Socket Mode, which is required for OAuth-based distribution.

1. Install [ngrok](https://ngrok.com/download) and start a tunnel:

```sh
ngrok http 3000
```

2. Copy the `https://*.ngrok-free.app` URL from the ngrok output.

<details><summary><strong>Using Slack CLI</strong></summary>

#### Slack CLI

3. Update `manifest.json` for HTTP mode:
   - Set `socket_mode_enabled` to `false`
   - Replace `ngrok-free.app` with your ngrok domain (e.g. `YOUR_NGROK_SUBDOMAIN.ngrok-free.app`)

4. Create a new local dev app:

```sh
slack install -E local
```

5. _(Slack CLI < v4.1.0 only)_ Enable MCP for your app:
   - Run `slack app settings` to open your app's settings
   - Navigate to **Agents & AI Apps** in the left-side navigation
   - Toggle **Model Context Protocol** on

6. Update your `.env` OAuth environment variables:
   - Run `slack app settings` to open App Settings
   - Copy **Client ID**, **Client Secret**, and **Signing Secret**
   - Update `SLACK_REDIRECT_URI` in `.env` with your ngrok domain

```sh
SLACK_CLIENT_ID=YOUR_CLIENT_ID
SLACK_CLIENT_SECRET=YOUR_CLIENT_SECRET
SLACK_SIGNING_SECRET=YOUR_SIGNING_SECRET
SLACK_REDIRECT_URI=https://YOUR_NGROK_SUBDOMAIN.ngrok-free.app/slack/oauth_redirect
```

7. Start the app:

```sh
slack run app_oauth.py
```

8. Click the install URL printed in the terminal to install the app to your workspace via OAuth.

</details>

<details><summary><strong>Using the Terminal</strong></summary>

#### Terminal

3. Create your Slack app at [api.slack.com/apps/new](https://api.slack.com/apps/new) using [`manifest.json`](./manifest.json). Before pasting the manifest, set `socket_mode_enabled` to `false` and replace `ngrok-free.app` with your ngrok domain.

4. Install the app to your workspace and copy the following values into your `.env`:
   - **Signing Secret** — from _Basic Information_
   - **Bot User OAuth Token** — from _OAuth & Permissions_
   - **Client ID** and **Client Secret** — from _Basic Information_

```sh
SLACK_BOT_TOKEN=xoxb-YOUR_BOT_TOKEN
SLACK_CLIENT_ID=YOUR_CLIENT_ID
SLACK_CLIENT_SECRET=YOUR_CLIENT_SECRET
SLACK_SIGNING_SECRET=YOUR_SIGNING_SECRET
SLACK_REDIRECT_URI=https://YOUR_NGROK_SUBDOMAIN.ngrok-free.app/slack/oauth_redirect
```

Replace `your-subdomain` in `SLACK_REDIRECT_URI` with your ngrok subdomain.

5. Start the app:

```sh
python3 app_oauth.py
```

6. Click the install URL printed in the terminal to install the app to your workspace via OAuth.

</details>

> **Note:** Each time ngrok restarts, it generates a new URL. You'll need to update the ngrok domain in `manifest.json`, `SLACK_REDIRECT_URI` in your `.env`, and re-install the app.

</details>

### Using the App

Once Groundswell is running, there are several ways to interact:

**App Home** — Open Groundswell in Slack and click the _Home_ tab. You'll see need-category buttons. Click one to open a modal, describe your educational need, and submit. Groundswell will build a coalition and post the results to a dedicated mission channel.

**Direct Messages** — Open a DM with Groundswell and describe an educational need. Groundswell will react with :eyes: while processing, then reply in a thread with a full coalition summary. Send follow-up messages in the same thread and Groundswell will maintain the full conversation context.

**Channel @mentions** — Invite Groundswell to a channel by typing `/invite @Groundswell` in the message box, then type `@Groundswell` followed by your need. Groundswell responds in a thread so the channel stays clean and automatically creates a mission channel for coordination.

**Assistant Panel** — Click _Add Agent_ in the top-right corner of Slack, select Groundswell from the list, then pick a suggested prompt or type a message.

Groundswell will add a :white_check_mark: reaction when it believes a mission has been resolved, and reacts with a contextual emoji to every message to keep things friendly.

### Linting

```sh
# Run ruff check from root directory for linting
ruff check

# Run ruff format from root directory for code formatting
ruff format
```

## Project Structure

### `manifest.json`

`manifest.json` is a configuration for Slack apps. With a manifest, you can create an app with a pre-defined configuration, or adjust the configuration of an existing app.

### `app.py`

`app.py` is the entry point for the application and is the file you'll run to start the server. This project aims to keep this file as thin as possible, primarily using it as a way to route inbound requests.

### `app_oauth.py`

`app_oauth.py` is an alternative entry point that runs the app in HTTP mode instead of Socket Mode. This is intended for deployments that use OAuth for app distribution. See the HTTP Mode section under Development for setup instructions.

### `manifest_oauth.json`

`manifest_oauth.json` is the app manifest configured for HTTP mode (Socket Mode disabled, with request URLs for event subscriptions and interactivity). Use this when setting up the app for HTTP mode instead of `manifest.json`.

### `/listeners`

Every incoming request is routed to a "listener". This directory groups each listener based on the Slack Platform feature used.

**`/listeners/events`** — Handles incoming events:

- `app_home_opened.py` — Publishes the App Home view with category buttons.
- `app_mentioned.py` — Responds to `@Groundswell` mentions in channels.
- `message.py` — Responds to direct messages from users.

**`/listeners/actions`** — Handles interactive components:

- `category_buttons.py` — Opens the issue submission modal when a category button is clicked.
- `feedback.py` — Handles thumbs up/down feedback on Groundswell's responses.

**`/listeners/views`** — Handles view submissions and builds Block Kit views:

- `issue_modal.py` — Processes modal submissions, starts a DM thread, and runs the agent.
- `app_home_builder.py` — Constructs the App Home Block Kit view.
- `modal_builder.py` — Constructs the issue submission modal.
- `feedback_block.py` — Creates the feedback button block attached to responses.

### `/agent`

The `casey.py` file defines the Pydantic AI Agent with a system prompt, personality, and tool configuration.

The `deps.py` file defines the `CaseyDeps` dataclass passed to the agent at runtime, providing access to the Slack client and conversation context.

The `tools` directory contains five IT support tools that the agent can call during a conversation.

### `/thread_context`

The `store.py` file implements a thread-safe in-memory conversation history store, keyed by channel and thread. This enables multi-turn conversations where Groundswell remembers previous context within a thread.

## Troubleshooting

### MCP Server connection error: `HTTP error 400 (Bad Request)`

If you see an error like:

```
Failed to connect to MCP server 'streamable_http: https://mcp.slack.com/mcp': HTTP error 400 (Bad Request)
```

This means the Slack MCP feature has not been enabled for your app. There is no manifest property for this yet, so it must be toggled on manually:

1. Run `slack app settings` to open your app's settings page (or visit [api.slack.com/apps](https://api.slack.com/apps) and select your app)
2. Navigate to **Agents & AI Apps** in the left-side navigation
3. Toggle **Slack Model Context Protocol** on
