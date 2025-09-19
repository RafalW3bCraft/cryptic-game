# TheFool — Rules of Engagement (RoE)

**Project:** TheFool — Legal Red-Team / Research Lab

**Author:** RafalW3bCraft

**Scope & Legalities**

1. **Authorized environment only**: All testing MUST be performed only inside the lab network described in this repo (`lab-net` / local docker environment). No scanning or testing of external IPs or cloud services without explicit, written authorization.

2. **Explicit permission**: Keep a signed (or at minimum - timestamped e-mail) record authorizing testing activities if using remote or institutional infrastructure.

3. **No real PII**: Do not use or include real personal data in datasets, prompts, or reports. Use synthetic data.

4. **No weaponized payloads**: Avoid creating or running malware, ransomware, or destructive payloads. Use benign traffic generators and C2 *simulators* for detection testing only.

5. **No social engineering**: The lab forbids social-engineering exercises against real humans.

**Allowed tests (lab-limited)**

- Browser-based testing: XSS, CSRF, session fixation, input validation on local Juice Shop and DVWA.
- Prompt injection & content leakage exercises ONLY against `mock-llm` service.
- API abuse testing (rate limits, auth flows) only on local mock endpoints.
- Network detection and IDS tuning (Suricata/Zeek) using generated synthetic traffic.

**Forbidden tests**

- Any scan, exploit, or payload that leaves the lab network.
- Use of cloud vendor APIs or vendor-hosted LLM endpoints without permission.
- Targeting third-party systems, universities, companies, or infrastructure.

**Data handling & reporting**

- All logs stored in `lab/logs/` and reports in `lab/reports/`.
- Sanitize request/response dumps to remove any real secrets or keys before sharing outside the lab.
- Follow responsible disclosure if recreating findings on systems outside the lab: document contact, give reasonable disclosure window, and avoid public posts that allow exploitation without a fix.

**Session rules**

- Every session must start with a `session-start` file containing operator, start time, and short goals.
- Every session must end with `session-end` noting actions, resets performed, and whether snapshots were restored.

**Emergency stop**

If a component unexpectedly attempts external network access or behaves in an unexpected way, immediately run `docker compose down`, isolate the host from the physical network, and capture forensic copies of logs before power-cycling.
