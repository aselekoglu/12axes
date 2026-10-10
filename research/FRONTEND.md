# Research frontend — preview route

The regular quiz is unchanged. Visit `/research` after starting both services:

```sh
# Terminal 1, repository root:
python -m pip install -r research/requirements.txt
uvicorn research.service:app --host 127.0.0.1 --port 8090

# Terminal 2:
cd frontend && npm ci && npm run dev
```

Visit http://localhost:5173/research. Vite proxies `/research-api/*` to port 8090.
Preview answers exist **only in React memory** and are never sent to any server.

Live enrollment is hidden unless `VITE_RESEARCH_ENABLE_ENROLLMENT=true`;
even then the independent research backend refuses any draft instrument and
requires approved study configuration. Do not use a generic consent checkbox as
a replacement for an independently reviewed full participant information statement.

Deploy research backend separately from the public Java API and set
`VITE_RESEARCH_API_URL` to its dedicated HTTPS origin only after external
review and production security testing. Do not put research server secrets into
Vite environment variables. Session tokens remain memory-only; production
UX must offer a reviewed accessible withdrawal/recovery channel.
