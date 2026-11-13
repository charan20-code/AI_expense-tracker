# Pennywise — Streamlit Expense Tracker

A beginner-friendly college mini-project built with **Streamlit**, **Python**, and **SQLite**. The app is a single Python file with no separate Flask backend. Streamlit runs it on your computer, SQLite saves expenses between runs, and the optional AI coach runs locally with Ollama.

## What it does

- Add expenses with a description, amount in rupees, category, and date.
- View total spending, expense count, and a category chart.
- Search expenses by description, category, or date.
- Delete a selected expense.
- Save data locally in `expenses.db`.
- Ask the optional local AI Spending Coach for insights based on aggregated totals.

## Requirements

- Windows 10 or 11
- Python 3.10 or newer, with pip included
- Visual Studio Code

## Open the project

1. Open VS Code and choose **File → Open Folder...**.
2. Select the `personal_expense_tracker` folder.
3. Choose **Terminal → New Terminal**.
4. Check Python and pip are available:

   ```powershell
   python --version
   python -m pip --version
   ```

   If either command fails, install Python for Windows from [python.org](https://www.python.org/downloads/), select **Add python.exe to PATH**, then close and reopen VS Code.

## Install and run

Run these commands in the VS Code PowerShell terminal, one at a time:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Streamlit will print a local address in the terminal. Open **http://localhost:8501** in your browser. The address works only on your computer while Streamlit is running. Keep the terminal open; press **Ctrl+C** there to stop the app. Start it again later with `streamlit run app.py`.

## Enable the AI Spending Coach

The coach runs on your computer using [Ollama for Windows](https://ollama.com/download/windows) and the `llama3.2:3b` model. Install Ollama, open a new VS Code terminal, then download the model once:

```powershell
ollama pull llama3.2:3b
```

Keep Ollama running while you use the tracker. Start the app as usual; open **AI Spending Coach** and ask a question. The coach sends the question and aggregated expense totals to Ollama at `localhost` on your computer. Expense details are not sent to an online AI service. This uses your computer's storage and processing power; response speed depends on your computer.

## Project files

```text
personal_expense_tracker/
├── app.py            Streamlit interface and SQLite storage
├── requirements.txt  Python packages
├── README.md         Setup and run instructions
└── expenses.db       Created automatically when the app first runs
```

To reset the app, stop it and delete `expenses.db`. This removes the saved expenses; a new empty database will be created the next time the app starts.
