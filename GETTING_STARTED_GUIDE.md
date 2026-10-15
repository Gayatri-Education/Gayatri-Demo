# GAYATRI PLATFORM v4.0.0 — GETTING STARTED & EVALUATION GUIDE

## 1. Supported Platform Policy

- **Supported Operating Systems:** Windows 10 (64-bit) or Windows 11 (64-bit)
- **Minimum Resolution:** 1366 × 768 (UI scaling 100%, 125%, 150% supported)
- **Processor:** Intel Core i3 / AMD Ryzen 3 or higher
- **RAM:** 4 GB minimum (8 GB recommended)
- **Disk Space:** 500 MB free space
- **Network:** None required (100% offline air-gapped execution)

> [!IMPORTANT]
> **Legacy Windows (Windows 7 / 8 / 8.1) Notice:**  
> Windows 7 reached end-of-life from Microsoft in January 2020. The underlying Chromium and Qt WebEngine runtimes do not support Windows 7. Running in legacy environments may trigger Chromium's "Need Windows 10 or later" browser infobar, blurry text, or unresponsive keyboard inputs. For guaranteed performance and security, run on Windows 10 or 11 (64-bit).

---

## 2. Choosing Your Launch Path

Gayatri provides two distinct execution options:

### Option A: Standalone Portable Release (NO Python Required)
*Recommended for evaluation, teachers, students, and institutional testing.*

The portable release is completely self-contained with bundled native runtimes. You **do not** need Python or pip installed on your machine.

1. Download `Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip` from official GitHub Releases.
2. Extract the ZIP to any local folder (e.g. `C:\Users\<user>\Desktop\Gayatri_Platform`).
3. Launch the application:
   - Double-click **`Gayatri_Launcher.bat`**, or
   - Double-click **`Gayatri.exe`** directly inside the extracted folder.
4. The frameless Gayatri desktop application window opens immediately.

### Option B: Developer Source Checkout (Requires Python 3.10+)
*For developers inspecting code, modifying curricula, or running test suites.*

If you downloaded the source repository (`GitHub Code → Download ZIP` or `git clone`), you need Python installed on your system.

#### 1. System Prerequisites
- Install **Python 3.10 to 3.12** from [python.org](https://www.python.org/downloads/).
- During installation, check the box: **"Add python.exe to PATH"**.

#### 2. Setup Virtual Environment (PowerShell or CMD)
Open PowerShell or Command Prompt in the repository folder:

```powershell
# Verify Python is available
python --version

# Create a clean virtual environment
python -m venv .venv

# Activate the virtual environment
# In PowerShell:
.\.venv\Scripts\Activate.ps1
# Or in Command Prompt:
.\.venv\Scripts\activate.bat

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### 3. Run Preflight Check & Launch
```powershell
# Run headless preflight verification
python -m app.main --check-startup

# Launch desktop application
python -m app.main
```

---

## 3. Recommended 5-Minute Evaluation Journey

1. **Welcome Screen:** Observe platform positioning ("AI-Powered Adaptive Learning Platform") and click **Enter Guided Showcase**.
2. **Engineering Mathematics:** Ask: *"Explain first-order differential equations and integrating factor"*. Inspect the **Retrieved Evidence** drawer on the right.
3. **Switch to Digital Electronics:** Click **Course Catalog** in the sidebar, select **Digital Electronics**, and ask: *"Explain universal gates NAND and NOR"*. Notice that knowledge grounding immediately switches to electronics with zero math cards.
4. **Test Adaptive Misconception Remediation:** Answer with an intentional misconception: *"For a NAND gate, the output is 0 when any input is 0"*. Observe that the Socratic tutor diagnoses the inversion flaw (*NAND/NOR Logic Inversion Error*) and guides your reasoning rather than leaking answers.
5. **Student Mastery Tracking:** Click **Student Mastery** in the sidebar. Verify dynamic mastery scoring, topic-level competency bars, and diagnosed misconceptions.
6. **Teacher Copilot:** Click **Teacher Copilot** in the sidebar to review class-wide misconception heatmaps and cohort alerts.
7. **Bring Your Curriculum:** Navigate to **Bring Curriculum** and click **Load Sample Curriculum Document** to test custom knowledge indexing.

---

## 4. Verifying Package Integrity & Windows Trust

Open PowerShell in the folder containing your downloaded release archive:

```powershell
# 1. Compute SHA-256 Hash
Get-FileHash -Path .\Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip -Algorithm SHA256

# 2. Compare against SHA256SUMS.txt
Get-Content .\SHA256SUMS.txt
```

If Windows SmartScreen displays an unrecognized app notice on first launch:
- Click **More info** $\to$ **Run anyway**.
- SmartScreen evaluates publisher and hash reputation over time per Microsoft guidelines.
- Scan the file with Microsoft Defender to confirm 0 threats detected.