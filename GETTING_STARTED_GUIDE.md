# GAYATRI PLATFORM v4.0.0 — GETTING STARTED & EVALUATION GUIDE

## 1. System Requirements

- **Operating System:** Windows 10 (64-bit) or Windows 11 (64-bit)
- **Processor:** Intel Core i3 / AMD Ryzen 3 or higher
- **RAM:** 4 GB minimum (8 GB recommended)
- **Disk Space:** 500 MB free space
- **Network:** None required (100% offline air-gapped execution)

---

## 2. Installation & Quickstart

### Method A: Portable ZIP (Recommended for Evaluations)
1. Download `Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip`.
2. Extract the archive to any folder (e.g. `C:\Users\<user>\Desktop\Gayatri_Platform`).
3. Double-click `Gayatri_Launcher.bat` or run:
   ```powershell
   python -m app.main
   ```
4. The frameless Gayatri application window will open immediately.

### Method B: Setup Installer
1. Download `Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup.exe`.
2. Run the installer. It installs per-user into `AppData\Programs\Gayatri AI` without requiring Administrator privileges.
3. Launch Gayatri AI from the Start Menu or Desktop shortcut.

---

## 3. Recommended 5-Minute Evaluation Journey

1. **Welcome Screen:** Observe the platform positioning ("AI-Powered Adaptive Learning Platform") and click **Enter Guided Showcase**.
2. **Engineering Mathematics:** Ask: *"Explain first-order differential equations and integrating factor"*. Inspect the **Retrieved Evidence** drawer on the right.
3. **Switch to Digital Electronics:** Click **Course Catalog** in the sidebar, select **Digital Electronics**, and ask: *"Explain universal gates NAND and NOR"*. Notice that knowledge grounding immediately switches to electronics with zero math cards.
4. **Test Adaptive Misconception Remediation:** Answer with an intentional misconception: *"For a NAND gate, the output is 0 when any input is 0"*. Observe that the Socratic tutor diagnoses the inversion flaw and guides your reasoning.
5. **Teacher Copilot:** Click **Teacher Copilot** in the sidebar to review class-wide misconception heatmaps and cohort alerts.
6. **Bring Your Curriculum:** Navigate to **Bring Curriculum** and click **Load Sample Curriculum Document** to test custom knowledge indexing.

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
- Scan the file with Microsoft Defender to confirm 0 threats.