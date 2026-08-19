# patmossoftware.com

Hand-written static site. **No build step** — GitHub Pages serves the repo root
straight from `main`, so what is committed is what is live.

Every page is one self-contained `index.html` with its stylesheet inline, and
makes no external requests: fonts are system stacks, the favicon and the mark
are inline SVG. That is deliberate, and worth keeping. It means a page cannot
break because something else went down, and there is nothing to rebuild before
a change goes out.

```
/                              studio home, leads with the current app
/shikaku/                      the app page
/blog/                         post index
/blog/<slug>/                  a post
/support/                      support and FAQ (linked from the App Store)
/privacy/                      privacy policy
/og.png                        default social preview
/shikaku/og.png                social preview for the app page and its post
/tools/make-og.py              regenerates both preview images
```

## Adding a post

Copy an existing post directory, change the content, and add an entry at the
top of the list in `blog/index.html`. There is no generator and no feed yet; at
one post a month that is cheaper than maintaining one.

Update all four of these in the new page's `<head>`, because they are what
every link preview reads: `<title>`, `description`, `canonical`, and the
`og:*` block.

## Social previews

`og.png` and `shikaku/og.png` are generated, not drawn by hand:

```bash
python3 tools/make-og.py     # needs Pillow
```

Both are 1200x630. The Shikaku one contains a real board, and the three
rectangles in it **must tile the grid exactly** — there is an assertion in the
script that fails if they do not. An image showing uncovered squares beside the
words "cover the whole grid" is the first thing a puzzle player will notice.

## Deploy

Push to `main`. Pages rebuilds within about a minute.

Settings that are already in place and should not need touching: **Settings →
Pages → Deploy from a branch → `main` / root**, with `CNAME` committed at the
root so the custom domain survives every deploy, `.nojekyll` so Jekyll does not
try to process anything, and Enforce HTTPS on.

## DNS

Apex `patmossoftware.com` — four A records:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

Optional AAAA for IPv6: `2606:50c0:8000::153`, `…8001::153`, `…8002::153`,
`…8003::153`. Plus a CNAME for `www` → `Matty-DB.github.io`.

## Screenshots

`shikaku/img/*.png` are resized from the App Store captures in the
`shikaku-game` repo (`AppStore/Screenshots/6.5-inch/`), scaled to 600px wide.
Capture them from the simulator rather than a phone — the status bar can only
be frozen on the simulator, so a real device leaves the actual time, battery
and carrier in the shot.
