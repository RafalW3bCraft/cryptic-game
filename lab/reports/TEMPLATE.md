# Title: [Short descriptive title]

- Date: YYYY-MM-DD HH:MM UTC
- Author: RafalW3bCraft (TheFool)
- Target: (e.g., juice-shop / mock-llm / dvwa)
- Environment: local TheFool Lab
- RoE reference: see ../ROE.md

## 1) Executive summary
One-paragraph description of the issue, impact, and location.

## 2) Affected component
- Name: juice-shop / mock-llm /dvwa
- Version: (if known)
- Endpoint or page: (URI)

## 3) Impact
Describe impact on Confidentiality / Integrity / Availability and real-world analogy.

## 4) Steps to reproduce (minimal)
1. Precise step 1 (include exact HTTP request if applicable)
2. Step 2
3. Expected result
4. Actual result

## 5) Evidence
- Request/response snippets (sanitized)
- Screenshots with annotations
- Suricata/Zeek log excerpts: (include timestamp + event id)

## 6) Root cause (brief)
Explain what component or misconfiguration allowed this.

## 7) Remediation & mitigation
- Short-term: quick config change or WAF rule
- Long-term: architecture / code fix
- Example config snippet (sanitized)

## 8) Severity & reproducibility
- Severity: Low / Medium / High
- Reproducibility: deterministic / intermittent / requires timing

## 9) Suggested tests after fix
List smoke tests and assertion checks to validate the remediation.

## 10) Appendices
- Full request/response logs (sanitized)
- Tooling notes: commands used, versions
