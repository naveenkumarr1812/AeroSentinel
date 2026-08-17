# AeroSentinel

AeroSentinel is an autonomous drone security and incident-response prototype built with Python, LangGraph, Streamlit, and a retrieval-augmented knowledge layer. It simulates a tactical mission workflow where a drone is selected, safety-checked, launched with human approval, and analyzed for threats such as people, vehicles, and perimeter violations.

## Overview

The project combines:

- a mission commander to interpret user requests
- a RAG knowledge layer for standard operating procedures
- agent-based memory and fleet coordination
- a safety gate to validate flight readiness
- human-in-the-loop approval checkpoints before launch and before critical decisions
- a simulation environment for drone activity and image review

## Project structure

- `app.py` — main Streamlit mission console UI
- `agents/` — autonomous system agents for command, safety, fleet, memory, and vision
- `graph/` — LangGraph workflow and state definitions
- `simulator/` — mock drone and fleet logic
- `rag/` — retrieval layer and SOP documents
- `memory/` — persistent mission history and state data
- `images/` — mission image assets used for simulated review

## Requirements

This project is designed to run in a Python virtual environment. A local `venv` folder is already present in the workspace, and it is excluded from git via the repository `.gitignore`.

## Local setup

1. Open a terminal in the project root.
2. Activate the virtual environment:

   PowerShell:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Start the Streamlit app:

   ```powershell
   streamlit run app.py
   ```

4. Or run the terminal mission flow:

   ```powershell
   python run_mission.py
   ```

## Environment variables

The project uses a Groq API key for AI access. Store it in a local `.env` file, for example:

```env
GROQ_API_KEY=your_api_key_here
```

Do not commit your `.env` file. It is ignored by git.

## Notes

- Human approval checkpoints are included so the mission can pause before launch and before high-risk decisions.
- The project includes a mocked fleet and image pipeline to simulate a security operations control room.
- Some generated vector-store files are ignored to avoid committing local runtime indexes.

## License

This project is licensed under the MIT License. See the [LICENCE](LICENCE) file for the full text.
