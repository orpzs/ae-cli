# ae-cli ⚡

> **Real-Time Conversational Streaming CLI for Vertex AI Agent Engine**

```
     _    _____        ____ _     ___ 
    / \  | ____|      / ___| |   |_ _|
   / _ \ |  _| _____ | |   | |    | | 
  / ___ \| |__|_____|| |___| |___ | | 
 /_/   \_\_____|      \____|_____|___|
  Vertex AI Agent Engine Interactive Terminal
```

`ae-cli` is a command-line interface for conversing with deployed Google Cloud Vertex AI Agent Engines (Reasoning Engines). It brings real-time token streaming, model reasoning thought blocks, tool call visualization, multi-turn session persistence, and slash commands directly to your terminal.

---

## 🚀 Quickstart

### 1. Install (one-time setup)

Clone the repository:
```bash
git clone https://github.com/orpzs/ae-cli.git
cd ae-cli
```

Install using **pip** or **uv**:

**Using pip:**
```bash
pip install -e .
```

**Using uv:**
```bash
uv pip install -e .
```
*(Or run directly without installing: `uv run ae`)*

### 2. Launch

```bash
ae
```

### ⚡ Automated First-Time Setup
When you run `ae` for the first time, it automatically guides you through:
1. **Google Cloud Authentication**: Logs in via `gcloud auth login` and sets up Application Default Credentials (ADC).
2. **Project & Region**: Selects your GCP Project ID and Vertex AI location.
3. **Agent Engine Selection**: Discovers your deployed Agent Engines in Vertex AI and lets you select one from a numbered list.

Once completed, you are dropped directly into the conversational chat session!

---

## 📖 Commands

| Command | Description |
| :--- | :--- |
| `ae` | Start interactive conversational chat session |
| `ae list` | List all deployed Agent Engines in your project |
| `ae query "prompt"` | Run a single query and stream response to stdout |
| `ae info` | Inspect deployed Agent Engine specs and callable methods |
| `ae sessions` | View saved conversation sessions |
| `ae setup` | Re-run authentication and switch target project/agent |
| `ae --version` | Show CLI version |

---

## 💬 Inside the Chat Terminal

While chatting, you can use built-in slash commands:

| Command | Description |
| :--- | :--- |
| `/help` | Show commands cheatsheet |
| `/new` | Start a new clean session on the Agent Engine |
| `/session` | View current session ID, user ID, and turn count |
| `/sessions` | List saved sessions for this agent |
| `/switch <id>` | Resume an existing conversation session |
| `/history` | View message history of current session |
| `/tools` | List tools and operations exposed by the agent |
| `/thoughts` | Toggle visibility of model thinking/reasoning blocks |
| `/raw` | Toggle raw JSON event stream (useful for debugging) |
| `/setup` | Switch active project or agent engine |
| `/clear` | Clear the terminal screen |
| `/exit` or `/quit` | Exit the chat session |

---

## 🔌 Pipelines & Scripting

Run one-off queries or pipe data directly through `ae`:

```bash
# Direct argument query
ae query "Summarize the latest sales metrics"

# Pipe from file or another CLI tool
cat transcript.txt | ae query

# Output raw JSON stream
ae query "Analyze data" --json
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
