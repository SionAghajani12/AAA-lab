# AAA Lab: Student Guide

**Authentication, Authorization and Accounting with Keycloak, Flask, Loki and Grafana**

Works on **macOS, Linux and Windows**. Time: about 90 minutes.

You will build a small company login system and answer the three questions of AAA:

| Question | Concept | In this lab |
| --- | --- | --- |
| Who are you? | Authentication | Keycloak: password + one-time code (MFA) |
| What are you allowed to do? | Authorization | Roles: `finance-viewer`, `finance-admin` |
| What did you do? | Accounting | Audit log shipped to Grafana |

**How the pieces fit together**

- **Docker** runs four services: Keycloak (logins), Loki (log storage), Alloy (log shipper), Grafana (log viewer).
- **Python** runs the finance app on your own computer. It sends you to Keycloak to log in and writes every action to `logs/audit.log`.
- **Alloy** reads that log file and pushes it to Loki. **Grafana** lets you search it.

> **Tip:** Use the tabs of your own system only. Each step shows commands for **macOS / Linux** and **Windows (PowerShell)** where they differ.

---

## Part A: Install the tools (once)

You need: **Docker**, **Python 3.9 or newer**, a **web browser**, and an **authenticator app** on your phone (Google Authenticator, FreeOTP or Aegis).

### A1. Install Docker

**macOS**

1. Install one of: Docker Desktop, OrbStack or Colima.
2. Open it and wait until it says Docker is running.

**Windows 10/11**

1. Install **Docker Desktop** from docker.com.
2. During setup keep **Use WSL 2** ticked. If asked, allow the restart.
3. Open Docker Desktop and wait until it says *Engine running*.

**Linux (Ubuntu/Debian example)**

1. Install Docker Engine and the Compose plugin by following docs.docker.com/engine/install for your distribution.
2. Allow your user to run Docker without `sudo`, then log out and log in again:

```bash
sudo usermod -aG docker $USER
```

### A2. Install Python 3

**macOS**

```bash
python3 --version
```

If it is missing, install from python.org or run `brew install python`.

**Windows**

1. Install Python from python.org.
2. **Tick "Add python.exe to PATH"** on the first installer screen.
3. Check in PowerShell:

```powershell
python --version
```

**Linux (Ubuntu/Debian)**

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### A3. Check everything works

Open a terminal (macOS/Linux: Terminal. Windows: **PowerShell**) and run:

```bash
docker --version
docker compose version
```

Both must print a version. Windows users: also run `python --version`. Others: `python3 --version`.

> **Checkpoint:** all three commands print a version and Docker is running.

---

## Part B: Prepare the lab folder

Your instructor gave you six files: `docker-compose.yml`, `config.alloy`, `loki.yml`, `app.py`, `requirements.txt`, and `LAB_GUIDE.md`.

**B1.** Create a folder named `aaa-lab` and these subfolders. The names must match exactly:

```
aaa-lab/
├── docker-compose.yml
├── alloy/
│   └── config.alloy
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── loki.yml
├── app/
│   ├── app.py
│   └── requirements.txt
└── logs/              (empty folder, you create it)
```

**macOS / Linux**

```bash
mkdir -p aaa-lab/alloy aaa-lab/grafana/provisioning/datasources aaa-lab/app aaa-lab/logs
```

**Windows (PowerShell)**

```powershell
mkdir aaa-lab\alloy, aaa-lab\grafana\provisioning\datasources, aaa-lab\app, aaa-lab\logs
```

**B2.** Move each file into place:

| File | Goes into |
| --- | --- |
| `docker-compose.yml` | `aaa-lab/` |
| `config.alloy` | `aaa-lab/alloy/` |
| `loki.yml` | `aaa-lab/grafana/provisioning/datasources/` |
| `app.py` | `aaa-lab/app/` |
| `requirements.txt` | `aaa-lab/app/` |

> **Important:** create the empty `logs` folder yourself **before** starting Docker. On Linux, if Docker creates it, it belongs to `root` and the app cannot write to it.
>
> **Windows:** keep the folder inside your user folder (for example `C:\Users\you\aaa-lab`) so Docker is allowed to share it.

> **Checkpoint:** the tree above matches what you see in your file explorer.

---

## Part C: Start the lab services

**C1.** Open a terminal **in the `aaa-lab` folder** and run:

```bash
docker compose up -d
docker compose ps
```

The first run downloads images and can take several minutes. You should see `keycloak`, `loki`, `alloy` and `grafana` as running. **Keycloak needs about a minute** before the website answers.

**C2.** Open http://localhost:8080 and log in with `admin` / `admin`.

> **Checkpoint:** you can see the Keycloak admin console.

---

## Part D: Build the company in Keycloak

All of this happens in your browser at http://localhost:8080.

**D1. Create a realm.** Click the dropdown at top left (it says *master*) > **Create realm**. Name: `company`. Create. **Keep `company` selected for every step below.**

**D2. Create roles.** Realm roles > **Create role**. Create `finance-viewer` and `finance-admin`.

**D3. Create users.** Users > **Add user**. For each user open the **Credentials** tab > **Set password** and turn **Temporary** off.

| Username | Password | Role (Role mapping tab > Assign role) |
| --- | --- | --- |
| alice | alice123 | finance-viewer |
| bob | bob123 | none |
| carol | carol123 | finance-admin |

**D4. Require MFA.**

1. Authentication > **Required actions**: for **Configure OTP**, turn on **Enabled** and **Set as default action**.
2. Users created before this need it added by hand: open alice, bob and carol one by one, add **Configure OTP** under *Required user actions*, and Save.

**D5. Record events.** Realm settings > **Events**: turn on **Save events** under *User events settings* and *Admin events settings*. Save.

**D6. Register the application.** Clients > **Create client**:

- Client type: OpenID Connect. Client ID: `finance-app`. Next.
- **Client authentication: ON.** Authentication flow: tick only **Standard flow**. Next.
- Root URL: `http://localhost:5000`
- Valid redirect URIs: `http://localhost:5000/*`
- Valid post logout redirect URIs: `http://localhost:5000/*`
- Web origins: `+`
- Save.
- Open the **Credentials** tab and **copy the Client secret**. You need it in the next part.

> **Checkpoint:** this address shows a block of JSON: http://localhost:8080/realms/company/.well-known/openid-configuration

---

## Part E: Run the finance app

Open a **new terminal window** (leave the Docker one alone). Go to the `app` folder, create a Python virtual environment, install the packages, set the secret and start the app.

**macOS / Linux**

```bash
cd aaa-lab/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export CLIENT_SECRET='paste-your-secret-here'
python app.py
```

**Windows (PowerShell)**

```powershell
cd aaa-lab\app
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:CLIENT_SECRET = 'paste-your-secret-here'
python app.py
```

If PowerShell says *running scripts is disabled*, run this once in the same window, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Windows (Command Prompt instead of PowerShell)**

```bat
cd aaa-lab\app
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
set CLIENT_SECRET=paste-your-secret-here
python app.py
```

Leave it running. Open http://localhost:5000.

> **Checkpoint:** you see "Finance System" and a login link.
>
> **Mac note:** if port 5000 is busy, turn off **AirPlay Receiver** in System Settings > General > AirDrop & Handoff.
>
> **Remember:** the secret is only set in *this* terminal window. If you close it, set it again before `python app.py`.

---

## Part F: Authentication ("Who are you?")

**F1.** Click **Log in with Keycloak**. Sign in as `alice` with her password.

**F2.** Keycloak shows a QR code. Scan it with your authenticator app, type the 6-digit code and give the device a name.

**F3.** You land on the Finance System. Notice "Signed in as alice" and her roles.

**F4.** Click **Log out**, then log in as alice again. Now you must enter your password **and** a code from your phone.

**Questions**

1. What are the two factors you used? (something you know / something you have)
2. After F1, which part of the system knew who alice was: the Flask app or Keycloak?

---

## Part G: Authorization ("What are you allowed to do?")

**G1.** Logged in as alice, click **Report**, then **Download CSV**. This works.

**G2.** Click **Admin**. You get **403 Forbidden**.

**G3.** Log out. Log in as `bob` (scan a new QR code for him), then click **Report**. Also 403.

**G4.** Log out. Log in as `carol` (set up OTP) and open **Admin**. It works.

**G5. Change a permission.** In Keycloak: Users > bob > Role mapping > Assign role > `finance-viewer`. In the app, bob is still blocked. Log out and log in again as bob, then open Report. It works now.

**Questions**

3. Alice and bob both logged in successfully. Why was bob still blocked from the report?
4. Why did bob's access only change after logging in again? (Hint: where are roles stored while you are logged in?)
5. Which principle says users should get only the access they need?

---

## Part H: Accounting ("What did you do?")

**H1.** Look at the raw log. In a terminal in the `aaa-lab` folder:

**macOS / Linux**

```bash
cat logs/audit.log
```

**Windows (PowerShell)**

```powershell
Get-Content logs\audit.log
```

Each line is one action: who, what, allowed or denied, when.

**H2.** Open Grafana: http://localhost:3000 > **Explore** > choose **Loki** > switch to the **Code** tab. Set the time range to *Last 15 minutes* and run each query:

```
{job="finance-app"} | json
{job="finance-app", result="denied"}
{job="finance-app", user="bob"}
{job="finance-app", action="download_report"}
```

**H3. Reconstruct the story.** Using only Grafana, write down for each user: when they logged in, what they accessed, what was denied.

**H4.** In Keycloak, open **Events**. This is the identity provider's own record: logins, OTP setup, role changes.

**Questions**

6. Who downloaded the report, and when?
7. Which attempts were denied, and why?
8. Why do we keep records of *denied* attempts, not only successful ones?

---

## Part I: Attack and detect

**I1.** Log out. At the login page enter a **wrong password** for alice at least 4 times.

**I2.** Check Keycloak > Events for `LOGIN_ERROR` entries. Try 10 or more wrong attempts. Does Keycloak lock the account? (Realm settings > Security defenses > Brute force detection is OFF by default. Turn it on, repeat, and compare.)

**Questions**

9. How could a company notice a password-guessing attack from logs?
10. Which part of AAA helped you detect it?

---

## Part J (optional): Look inside a token

In `app/app.py`, find the `callback()` function and add this line right after `token = ...`:

```python
print(token["access_token"])
```

Stop the app (`Ctrl+C`), start it again, log in, copy the token printed in the terminal and paste it into https://jwt.io (**lab tokens only, never real ones**). Find `preferred_username` and `realm_access.roles`. This is the evidence the app uses to answer "who are you" and "what may you do".

---

## Final reflection

Write one sentence each:

1. Where in this lab did **Authentication** happen?
2. Where did **Authorization** happen?
3. Where did **Accounting** happen?
4. Would this system still be secure if the audit log were stored only on the finance app server? Why or why not?

---

## Clean up

Stop the Flask app with `Ctrl+C` (and type `deactivate` to leave the virtual environment). Then, in the `aaa-lab` folder:

```bash
docker compose down        # stop, keep data
docker compose down -v     # stop and erase everything
```

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `docker: command not found` or "cannot connect to the Docker daemon" | Start Docker Desktop / OrbStack / Colima and wait until it says running. Linux: `sudo systemctl start docker`. |
| Linux: "permission denied" talking to Docker | Run `sudo usermod -aG docker $USER`, then log out and in again. |
| Windows: Docker Desktop will not start | Enable virtualization in BIOS and install WSL 2 (`wsl --install` in an admin PowerShell, then restart). |
| `python` not found (Windows) | Reinstall Python with **Add python.exe to PATH** ticked, then open a new PowerShell. |
| `python3` not found (Windows) | Use `python` instead. |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. |
| `KeyError: 'CLIENT_SECRET'` | Set `CLIENT_SECRET` in the **same terminal** as `python app.py`. |
| Invalid redirect\_uri | Re-check the client's redirect URI: `http://localhost:5000/*` |
| Invalid client credentials | Copy the secret again from Clients > finance-app > Credentials. |
| Keycloak page will not load | Wait another minute. Check `docker compose logs keycloak`. |
| "Port is already allocated" for 8080 or 3000 | Another program uses that port. Close it, or run `docker compose down` and try again. |
| No QR code at login | Add *Configure OTP* to the user's required actions, then log out. |
| Roles look wrong | Log out and log in again; roles are read at login. |
| Authenticator code rejected | Your computer clock must be correct. Turn on automatic time. |
| Grafana shows no logs | Check that `logs/audit.log` exists (use the app first), set range to Last 15 minutes, then run `docker compose logs alloy`. |
| Linux: app cannot write the log | The `logs` folder is owned by root. Run `sudo chown -R $USER logs` and try again. |
| Port 5000 busy (Mac) | Turn off AirPlay Receiver in System Settings > General > AirDrop & Handoff. |
