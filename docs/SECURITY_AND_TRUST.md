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

## 3. Microsoft SmartScreen Reputation Guidance

Per current Microsoft documentation ([SmartScreen Reputation for Windows App Developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)):
- SmartScreen evaluates both digital signature publisher reputation and individual file hash reputation.
- Brand-new public software releases may display an unrecognized application notice initially until reputation accumulates across downloads.
- Gayatri provides cryptographic SHA-256 checksums in `SHA256SUMS.txt` allowing administrators to verify binary integrity independently before execution.

---

## 4. Verification Commands for Evaluators

```powershell
# 1. Verify SHA-256 Checksum
Get-FileHash -Path .\dist\Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip -Algorithm SHA256

# 2. Run Microsoft Defender Scan
& "C:\ProgramData\Microsoft\Windows Defender\Platform\*\MpCmdRun.exe" -Scan -ScanType 3 -File .\dist

# 3. Verify Offline / Air-Gapped Mode
pytest tests/security/test_network_audit.py -v
```