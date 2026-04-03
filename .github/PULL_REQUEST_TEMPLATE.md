## WHAT
<!-- What was built in this PR? One paragraph. -->

## WHY
<!-- Protocol or design rationale. Why this approach over alternatives? -->

## REAL OUTPUT
<!-- Paste actual MCP request/response JSON or test output. No placeholders. -->
```json
{
  "request": {},
  "response": {}
}
```

## HOW TO TEST
```bash
cp .env.example .env
docker-compose up --build -d
make test-integration
```

## Checklist

- [ ] Conventional commit messages on every commit
- [ ] No secrets in code or `.env` (only `.env.example`)
- [ ] Integration tests pass against live server
- [ ] CHANGELOG.md updated
- [ ] Docs updated if new tool or schema change