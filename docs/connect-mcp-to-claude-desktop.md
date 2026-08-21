# Connecting Claude Desktop to Our Local Urbangreen MCP Server

This guide walks through connecting Claude Desktop to our locally-run Urbangreen MCP server (Python, running in Docker, exposed over plain HTTP on `localhost:8001`).

Since our server is `http://` and not `https://`, Claude Desktop can't reach it directly through the "Custom Connector" URL field (that path requires a public HTTPS endpoint). Instead, we use `mcp-remote`, a small local bridge that runs alongside Claude Desktop and forwards requests to our server over `localhost`. This requires Node.js to be installed.

Follow the steps in order — steps 4 and 6 are the ones people usually get wrong, so pay close attention there.

---

## 1. Install Node.js

`mcp-remote` runs via `npx`, which comes with Node.js. If you don't already have Node installed:

- Download the **LTS version** from **[nodejs.org](https://nodejs.org/en/download)**
- Run the installer with default options
- Verify it worked by opening a terminal (Command Prompt / Terminal) and running:
  ```
  node -v
  npx -v
  ```
  Both should print a version number.

## 2. Download and install Claude Desktop

- Download the app from **[claude.ai/download](https://claude.ai/download)** (Windows or Mac — do not use any third-party download source)
- Run the installer and launch the app

## 3. Sign in

- Open Claude Desktop and sign in with your Anthropic account (same login you use on claude.ai)

## 4. Find and open the config file

Local MCP servers are configured through a file called `claude_desktop_config.json`.

**Best way to open it:** in Claude Desktop, go to **Settings → Developer → Edit Config**. This opens the correct file directly and creates it if it doesn't exist yet.

If you want to find it manually, or the button doesn't work, the default locations are:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

> **Note on Windows:** some installs use a virtualized path instead — `%LOCALAPPDATA%\Packages\...\LocalCache\Roaming\Claude\claude_desktop_config.json`. In practice, the file opened by the **Edit Config** button (option above) is the one that matters — use that one. Only check the virtualized path as a fallback if the app doesn't seem to pick up your changes at all.

## 5. Add the MCP server config

Open the file in a text editor and add an `mcpServers` block. **If the file already has content** (e.g. other settings), add `mcpServers` as a new top-level key rather than replacing everything — just make sure the JSON stays valid (commas between keys, matching braces).

If the file is empty or new, use exactly this:

```json
"mcpServers": {
  "urbangreen-mcp": {
    "command": "npx",
    "args": ["-y", "mcp-remote", "http://localhost:8001/mcp"]
  }
}
```

If you already have other entries in the file, just add the `urbangreen-mcp` block inside your existing `mcpServers` object (or add `mcpServers` as a new key if you don't have one yet). Ask in the team channel if you're not sure your JSON is valid — a misplaced comma will silently break the whole file.

## 6. IMPORTANT — fully quit and restart Claude Desktop

Claude Desktop only loads MCP servers on startup, and it **caches the connection** — simply closing the window is not enough.

- **Windows:** Close the window, then right-click the Claude icon in the system tray (near the clock, bottom-right) and choose **Quit**. If it's still running afterward, open **Task Manager** (Ctrl+Shift+Esc), find `Claude` in the process list, and **End Task**.
- **Mac:** Press **Cmd+Q** while Claude is focused (closing the window with the red button is not enough — the app keeps running in the background). If unsure, check the Dock/Activity Monitor to confirm it's fully closed.

Once it's fully closed, reopen Claude Desktop normally.

## 7. Verify it worked

After restarting:

- Click the **"+" button** at the bottom-left of the chat box → **Connectors**, and check that `urbangreen-mcp` appears there. If it's off, toggle it on for your conversation.
- Or go to **Settings → Developer** — you should see `urbangreen-mcp` listed with a status (running/error) and a link to its logs.
- Start a new chat and ask Claude to list its available tools — you should see tools from our MCP server.

## Troubleshooting

- **Server shows an error / doesn't appear at all:** Check the logs via Settings → Developer. Common causes:
  - `npx` not found → Node.js isn't installed or isn't on your PATH (re-check step 1)
  - Connection refused → make sure the Docker container is actually running and port `8001` is published to your host machine (`-p 8001:8001` in your `docker run`/`docker-compose`), not just exposed inside the Docker network
- **Nothing changed after editing the config:** You likely didn't fully quit the app — repeat step 6 carefully
- **JSON errors:** Validate your file (a trailing comma is the most common mistake) using any online JSON validator before restarting
