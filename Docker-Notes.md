# Docker Installation and Setup Guide for Windows

## Step 1: Install WSL

1. Open the **Start Menu**.

2. Search for **PowerShell**.

3. Open PowerShell and enter the following command:

   ```powershell
   wsl --install
   ```

4. Press **Enter** and wait for the installation to complete.

5. If Windows asks you to restart your computer, save your work and restart it.

**Note:** WSL (Windows Subsystem for Linux) allows you to run a Linux environment on Windows and is required for the standard Docker Desktop setup using the WSL 2 backend.

## Step 2: Run PowerShell as Administrator

1. Open the **Start Menu**.
2. Search for **PowerShell**.
3. Right-click **Windows PowerShell** or **PowerShell**.
4. Select **Run as administrator**.
5. If the User Account Control (UAC) prompt appears, click **Yes**.
6. Copy and paste the provided Docker installation or configuration command into the PowerShell window.
7. Press **Enter** and wait for the command to finish.
8. If prompted, restart your computer to apply the changes.

**Important:** Run only the command provided by your instructor or from a trusted source. Review the command before executing it, especially if it downloads or runs a script.

## Step 3: Configure the Required Windows Settings

1. Open **Settings** by pressing `Win + I`.
2. Navigate to **System**.
3. Open the relevant advanced system settings or configuration section specified by your instructor.
4. If Windows requests administrator credentials, enter the required password or approve the permission prompt.
5. Follow the provided instructions to complete the configuration.

**Note:** The exact location of the advanced settings depends on which configuration is required. If this step refers to Docker Desktop, open Docker Desktop and check its settings for the WSL 2 integration options.

## Step 4: Verify the Installation

After completing the previous steps, open PowerShell and run:

```powershell
wsl --status
```

To check whether Docker is installed and available, run:

```powershell
docker --version
```

If Docker Desktop is installed and running, verify that the Docker engine is working:

```powershell
docker run hello-world
```

If the command succeeds, Docker will download and run a test image and display a confirmation message.
