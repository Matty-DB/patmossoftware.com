# patmossoftware.com

Coming-soon one-pager. Single self-contained `index.html` — no build step, no external requests
(fonts are system stacks, favicon and logo are inline SVG).

## Deploy to GitHub Pages

```bash
cd ~/Documents/_AppDev/patmossoftware.com
git init && git add -A && git commit -m "Coming soon page"
gh repo create patmossoftware.com --public --source=. --push
```

Then in the repo: **Settings → Pages → Source: Deploy from a branch → `main` / `root`**.

The `CNAME` file is already committed, so Pages picks up the custom domain automatically.
Once DNS resolves, tick **Enforce HTTPS** (may take up to ~24h for the cert to issue).

## DNS at your registrar

Apex `patmossoftware.com` — four A records:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

(Optional AAAA for IPv6: `2606:50c0:8000::153`, `…8001::153`, `…8002::153`, `…8003::153`)

Plus a CNAME for `www` → `<your-github-username>.github.io`

## Before it goes live — edit these

- `hello@patmossoftware.com` (3 places in `index.html` + footer) — set up the mailbox, or swap to your Proton address
- The tagline in `<p class="tagline">`
- `og.png` — 1200×630 social preview image, referenced in the head but not yet created
