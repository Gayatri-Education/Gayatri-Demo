# GAYATRI PLATFORM v4.0.0 — SECURITY, ANTIVIRUS & ENTERPRISE TRUST

## 1. Security Architecture Summary

Gayatri Platform v4.0.0 is engineered specifically for institutional and enterprise environments requiring strict data sovereignty, privacy compliance, and air-gapped stability.

### 1.1 Zero Outbound Data Egress (Strict Air-Gap)
- The application executes 100% offline.
- No telemetry, analytics, crash reporting, or external API pings exist in the codebase.
- Verified in automated test `tests/security/test_network_audit.py::test_air_gapped_offline_execution`.

### 1.2 Strict Loopback Local Networking
- The internal service and Qt WebEngine bridge bind exclusively to `127.0.0.1` (loopback).
- Binding to `0.0.0.0` is strictly prohibited.
- **Firewall Impact:** The application does not trigger Windows Defender Firewall public/private inbound access prompts.

### 1.3 Memory-Bounded Document Ingestion Sandbox
- Supported formats: PDF, DOCX, TXT, Markdown.
- Maximum upload size strictly capped at 5 MB (`RAG_MAX_UPLOAD_BYTES = 5 * 1024 * 1024`).
- Sanitized filenames prevent directory traversal attacks (`../../`).
- Parsed text is scanned and stripped of executable payloads and control characters.

---

## 2. Antivirus & SmartScreen False-Positive Mitigation

Previous legacy releases (v3.x) encountered false-positive warnings from heuristic antivirus engines due to executable packing (UPX) and bundled raw binary weights. Gayatri v4.0.0 implements an anti-false-positive engineering protocol:

1. **No Binary Packing (No UPX):** The PyInstaller build specification explicitly enforces `upx=False`. All portable binaries and DLLs remain uncompressed in standard PE format.
2. **Transparent File Structure:** The application distribution contains clear, un-obfuscated modular assets.
3. **Clean-Room Microsoft Defender Verification:**
   - **Scanner:** `MpCmdRun.exe` (Microsoft Defender Platform)
   - **Command:** `MpCmdRun.exe -Scan -ScanType 3 -File "<release_dir>"`
   - **Result:** **0 Threats Found (Scan Clean)**

---

## 3. Anti-Reverse Engineering & Intellectual Property Protection

Enterprise deployments often require preventing reverse engineering of proprietary pedagogical rules, internal system prompts, and institutional curriculum content. Gayatri v4.0.0 implements an anti-reverse engineering pipeline:

1. **Native PE Executable Distribution:** All application logic is compiled into standard Windows PE binaries. Zero loose Python source code (`.py`) files are distributed within the release package.
2. **Bytecode Stripping & Optimization:** The PyInstaller build specification compiles with `-OO` optimization, stripping Python docstrings, asserts, variable annotations, and debug symbol metadata.
3. **Encapsulated Binary Curriculum Container:** Institutional course packages, knowledge cards, and syllabus definitions are compiled into an obfuscated and compressed container (`demo_data/courses.dat`) featuring magic-header verification (`GYTR_CRSE_v4`), byte masking, and zlib compression. Loose plaintext JSON cards are eliminated from release packages.
4. **Volatile In-Memory Loading:** Knowledge graphs and RAG indices are hydrated directly in volatile RAM without staging temporary plaintext files to the filesystem.
5. **Automated Pipeline Audit:** The release build pipeline (`scripts/build_demo.py`) includes strict automated assertions that inspect the generated release bundle and abort the build if any loose `.py` source file or plaintext JSON curriculum card is detected.

---

## 4. Microsoft SmartScreen Reputation Guidance

Per current Microsoft documentation ([SmartScreen Reputation for Windows App Developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartScreen-reputation)):
- SmartScreen evaluates both digital signature publisher reputation and individual file hash reputation.
- Brand-new public software releases may display an unrecognized application notice initially until reputation accumulates across downloads.
- Gayatri provides cryptographic SHA-256 checksums in `SHA256SUMS.txt` allowing administrators to verify binary integrity independently before execution.

---

## 5. Verification Commands for Evaluators

```powershell
# 1. Verify SHA-256 Checksum
Get-FileHash -Path .\dist\Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip -Algorithm SHA256

# 2. Run Microsoft Defender Scan
$mp = (Get-ChildItem -Path "C:\ProgramData\Microsoft\Windows Defender\Platform" -Filter "MpCmdRun.exe" -Recurse | Select-Object -First 1).FullName
& $mp -Scan -ScanType 3 -File .\dist

# 3. Verify Offline / Air-Gapped Mode & Zero Reverse Engineering Leakage
pytest tests/ -v
```