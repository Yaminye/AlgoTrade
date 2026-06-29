# Getting Started — From Zero (Complete Beginner Guide)

This guide assumes you have **no programming experience**. We go step by step, from installing the
tools to running the app in your browser. Follow the order; don't skip steps.

> ⏱️ Estimated time: 10–20 minutes (mostly downloads and installs).
> 💰 Cost: you need to load at least **$5** into Anthropic (the only part that costs money). The FMP key is free.
>
> ✅ **Already have something installed?** If a tool from a step is already on your computer
> (Python, an editor, git…), you can **skip that step** and move on.

---

## Table of contents

1. Overview — what's going to happen
2. Install Python
3. Install a code editor (VS Code)
4. Download the project
5. Open the project and the terminal
6. Install the project's packages
7. Get an Anthropic API key (including loading $5)
8. Get an FMP API key (free)
9. Add the keys to the project
10. Run the app
11. Basic usage
12. Stopping and re-running next time
13. Common troubleshooting

---

## 1. Overview — what's going to happen

The app is written in **Python**. To run it you need to:

- Install Python (the language itself).
- Install a code editor to open and run it — we'll use **VS Code**.
- Download the project files.
- Install the "packages" the project needs (helper libraries).
- Get two API keys (passwords for external services).
- Run one command — and the app opens in your browser.

---

## 2. Install Python

> ✅ **Skip this step** if you already have Python 3.11+ — check with `python --version`
> (or `python3 --version`) in a terminal.

### Windows

1. Go to:

   ```
   https://www.python.org/downloads/
   ```

2. Click the yellow **Download Python** button (version 3.11 or newer).
3. Run the downloaded file.
4. **Very important:** in the installer, tick the **Add Python to PATH** checkbox at the bottom
   before clicking Install.
5. Click **Install Now** and wait for it to finish.

### Mac

1. Go to the same site:

   ```
   https://www.python.org/downloads/
   ```

2. Download the macOS version, run the file, and click Continue / Install to the end.

### Verify it worked

Open a command window (Windows: search the Start menu for **cmd**; Mac: open **Terminal**) and type:

```bash
python --version
```

If you see something like `Python 3.12.0` — great. (On Mac, if that didn't work, try `python3 --version`.)

---

## 3. Install a code editor (VS Code)

> ✅ **Skip this step** if you already have VS Code (or another editor like PyCharm) installed.

1. Go to:

   ```
   https://code.visualstudio.com/
   ```

2. Click **Download** (it auto-detects Windows/Mac), run the file, and install.
3. Open VS Code after installing.

> You can use PyCharm or another editor instead, but VS Code is simpler for beginners — we'll continue with it.

---

## 4. Download the project

There are two ways. The easy one is downloading a ZIP.

### Easy way — download ZIP

1. Open the project page on GitHub.
2. Click the green **Code** button, then **Download ZIP**.
3. Extract the ZIP to a folder you'll find easily, e.g. the Desktop.

### Advanced way — git clone (optional)

> ✅ Only if git is already installed.

```bash
git clone <repo-url>
```

---

## 5. Open the project and the terminal

1. In VS Code: menu **File → Open Folder...**
2. Choose the project folder (the folder named `AlgoTrade` that contains the file `app.py`).
3. Open a terminal inside VS Code: menu **Terminal → New Terminal**. A command window opens at the
   bottom, already inside the project folder.

From now on, type all commands in this terminal.

---

## 6. Install the project's packages

We'll create a "virtual environment" (a separate library folder just for this project) and then
install the packages.

### Windows

Type line by line (Enter after each):

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Mac

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

After activating the environment, `(venv)` should appear at the start of the terminal line. The last
command (`pip install`) takes a minute or two — wait for it to finish.

---

## 7. Get an Anthropic API key (including loading $5)

This is the key that powers the AI.

1. Go to:

   ```
   https://console.anthropic.com
   ```

2. Sign up / log in (you can use a Google account).
3. In the menu, go to **Billing** and add a payment method.
4. Load credit — **minimum $5** (Add credits / Buy credits).
5. Go to **API Keys**, click **Create Key**, give it any name, and click Create.
6. **Copy the key immediately** (it starts with `sk-ant-...`). It is shown only once — save it
   temporarily in a notes app.

> 💡 Each "AI comparison" uses a little credit. $5 is plenty for many test runs.

---

## 8. Get an FMP API key (free)

This is the key that fetches the historical financial data.

1. Go to:

   ```
   https://site.financialmodelingprep.com/developer/docs
   ```

2. Sign up for free (Sign Up / Get my API Key).
3. After signing up, your **API Key** appears on the Dashboard — copy it.

---

## 9. Add the keys to the project

1. In VS Code's file list (left side), check whether a folder named `.streamlit` exists.
   If not — create it: right-click an empty area → **New Folder** → name it `.streamlit`
   (with a leading dot).
2. Inside `.streamlit`, create a new file named `secrets.toml`
   (right-click `.streamlit` → **New File** → `secrets.toml`).
3. Paste the two lines below, replacing the text with the real keys you copied:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   FMP_API_KEY = "your-fmp-key-here"
   ```

4. Save the file (Ctrl+S / Cmd+S).

> 🔒 **Important security note:** `secrets.toml` contains real passwords.
> - Don't share it and don't upload it to GitHub.
> - The project is already set to ignore this file (`.gitignore`), so it won't be part of the
>   submission — which is correct and intended.
> - If a key is ever exposed, revoke it and create a new one.

---

## 10. Run the app

Make sure you're still in the terminal with `(venv)` at the start of the line, and type:

```bash
streamlit run app.py
```

After a few seconds a browser opens automatically with the app. If it doesn't, open a browser
manually and go to:

```
http://localhost:8501
```

🎉 That's it — the app is running.

---

## 11. Basic usage

- On the right (Sidebar) choose a stock by ticker or company name.
- Navigate the tabs: Chart, Financials, Valuation, Compare, Analysts, Holders, Profile.
- The Sidebar has an **AI assistant** — ask it freely about a sector, company, or news.
- In the **Compare** tab: pick a few stocks, click **Show data**, then **AI comparison** to get an
  analysis and recommendation.

---

## 12. Stopping and re-running next time

### To stop

In the terminal press `Ctrl + C`.

### To run again tomorrow

No need to reinstall. Just open the folder in VS Code, open a terminal, and re-activate the
environment, then start the app:

**Windows:**

```bash
venv\Scripts\activate
streamlit run app.py
```

**Mac:**

```bash
source venv/bin/activate
streamlit run app.py
```

---

## 13. Common troubleshooting

**`python` is not recognized / command not found**
"Add Python to PATH" wasn't ticked during install. Reinstall Python and tick the box. On Mac try `python3`.

**`pip install` fails / hangs**
Make sure you have internet and that `(venv)` is shown on the line. Run the command again.

**`streamlit: command not found`**
You forgot to activate the virtual environment. Run the activate command first (section 12), then
`streamlit run app.py` again.

**Key error — ANTHROPIC_API_KEY / FMP_API_KEY missing**
The keys weren't added correctly. Check that the file is exactly at `.streamlit/secrets.toml`, that
its name is exact, and that the keys are in quotes.

**Port is busy (Port 8501 is already in use)**
The app is already running in another window, or a previous run didn't close. Close earlier
windows/terminals and try again.

**The assistant / comparison returns an error**
Usually low Anthropic credit or a wrong key. Check your balance in Billing, and that the key was
copied in full.

---

## Authors

Yehonatan · Ido · Idan
