# TheFool — Legal Red-Team / Research Lab

**Author:** RafalW3bCraft
**License:** MIT

## Quick start

1. Ensure Docker & Docker Compose are installed.
2. Clone the repo and run: `docker compose up -d --build`
3. Access:
   - Juice Shop: http://localhost:3000
   - Mock LLM: http://localhost:5000/v1/generate (POST JSON {"prompt":"..."})
   - Kibana: http://localhost:5601 (if ELK is up)

Follow `ROE.md` for rules of engagement. Use `lab/reports/TEMPLATE.md` for reporting findings.
