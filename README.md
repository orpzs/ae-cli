# ae-cli ⚡

> **Real-Time Conversational Streaming CLI for Vertex AI Agent Engine**

---

```
     _    _____        ____ _     ___ 
    / \  | ____|      / ___| |   |_ _|
   / _ \ |  _| _____ | |   | |    | | 
  / ___ \| |__|_____|| |___| |___ | | 
 /_/   \_\_____|      \____|_____|___|
  Vertex AI Agent Engine Interactive Terminal
```

`ae-cli` is a developer-centric command-line interface for conversing with deployed Google Cloud Vertex AI Agent Engines (Reasoning Engines). It brings the fluid streaming, reasoning thought blocks, tool call visualization, multi-turn session persistence, and slash commands of modern AI coding assistants straight to your terminal.

---

## ✨ Features

- 🔄 **Real-Time Streaming Output**: Streams tokens chunk-by-chunk over pure REST Server-Sent Events (SSE).
- 🧠 **Thought & Reasoning Display**: Formats model thinking tokens in styled, collapsible thought blocks.
- ⚙️ **Action & Tool Execution Visualizer**: Highlights function calls, arguments, and returned results in real time.
- 💬 **Interactive REPL Session**: Conversational chat loop with command history, arrow key navigation, and slash commands.
- 🗂️ **Multi-Turn Session Continuity**: Automatically manages session state on Vertex AI or resumes previous sessions.
- 🛡️ **Enterprise Ready**: Built on pure HTTP/REST SSE streaming—completely immune to corporate Windows WDAC / AppLocker blocks on `cygrpc.pyd`.
- 🔌 **Script & Pipeline Friendly**: Run single-shot queries (`ae query "..."`) or pipe input directly (`cat data.txt | ae query`).

---

## 🚀 Quickstart

### 1. Installation

Clone or navigate to the repository and install in editable mode:

```bash
cd ae-cli
pip install -e .
```

> **Windows Tip**: On machines with Windows Defender Application Control (WDAC), you can run via `.\ae.bat`, `.\ae.ps1`, or `python -m ae_cli.main`.

### 2. Configuration

Set your Google Cloud project and region via environment variables or a `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```dotenv
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional: default target agent
AGENT_ENGINE_ID=1234567890123456789
# or match by display name:
APP_NAME=Transcript Summarizer
```

Ensure you have Google Cloud credentials:
```bash
gcloud auth application-default login
```

---

## 📖 Usage

### 1. Interactive Conversational Chat (Default)

Launch the interactive chat terminal:

```bash
# Connect to agent by ID
ae chat --engine 1234567890123456789

# Or connect by Display Name
ae chat --app "Transcript Summarizer"

# Or simply run 'ae' if configured in .env
ae
```

### 2. Slash Commands in Interactive Mode

While inside the interactive chat loop, you can use built-in slash commands:

| Command | Description |
| :--- | :--- |
| `/help` | Show available slash commands and keyboard shortcuts |
| `/new` | Start a new clean conversation session on the Agent Engine |
| `/session` | View current session ID, user ID, and turn count |
| `/sessions` | List all locally saved sessions for this agent |
| `/switch <id>` | Switch to an existing conversation session |
| `/history` | View message history of the current session |
| `/info` | Inspect deployed Agent Engine metadata, specs, and requirements |
| `/tools` | List registered tools and operations exposed by the agent |
| `/thoughts` | Toggle visibility of model thinking/reasoning blocks |
| `/raw` | Toggle raw JSON event streaming (useful for agent debugging) |
| `/clear` | Clear terminal screen |
| `/exit` or `/quit` | Cleanly exit the interactive session |

---

### 3. Single-Query Mode (Pipeable)

Execute a one-off query without entering the interactive loop:

```bash
# Direct argument query
ae query "Summarize the latest sales report"

# Pipe input from a file or another command
cat transcript.txt | ae query

# Output raw JSON array of stream events
ae query "Find discrepancies" --json
```

---

### 4. Agent Engine Management

#### List Deployed Agent Engines
```bash
ae list
```
Displays a table with display names, resource IDs, creation times, and update timestamps.

#### Inspect Agent Specifications
```bash
ae info 1234567890123456789
```
Displays deployment specs, python runtime, dependencies, and registered callable class methods.

#### List Saved Conversation Sessions
```bash
ae sessions
```

---

## 🛠️ Architecture

```
ae-cli
├── ae_cli/
│   ├── client.py        # Vertex AI REST SSE Streaming Client & Event Normalizer
│   ├── auth.py          # Google Cloud ADC, gcloud CLI, and Token Resolver
│   ├── session.py       # Session State & Turn History Persistence
│   ├── config.py        # Environment & CLI Configuration Loader
│   ├── ui/
│   │   ├── console.py   # Rich Console, ASCII Banners, and Alert Styling
│   │   ├── renderer.py  # Real-Time Stream, Thought & Tool Call Renderer
│   │   └── prompt.py    # prompt_toolkit REPL with History & Slash Commands
│   └── commands/
│       ├── chat.py      # Interactive Conversational Loop
│       ├── query.py     # Single-Shot & Pipeable Query Handler
│       ├── list_agents.py # Agent Engine Discovery
│       └── info.py      # Agent Specification Inspector
```

---

## 🧪 Testing

Run the test suite:

```bash
python -m unittest discover tests
```

---

## 📄 License

Apache 2.0
