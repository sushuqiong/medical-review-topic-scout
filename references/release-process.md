# Release Process

Use this lightweight process when publishing a new version of `medical-review-topic-scout`.

## 1. Update project files

- update `README.md` if the scanner workflow or output interpretation changed
- update `CHANGELOG.md`
- update changed files under `references/`, `scripts/`, or `assets/`

## 2. Prepare release notes

Start from:

- `.github/release-template.md`

Keep the final note short, concrete, and readable for people browsing GitHub.

## 3. Structure to preserve

A good release note for this repo usually includes:

1. one-sentence summary
2. highlights
3. added
4. improved
5. fixed
6. who this helps
7. recommended next step

## 4. Good style for this repo

- focus on evidence-first topic scouting
- mention PubMed limitations when relevant
- distinguish topic screening from formal proof of novelty
- keep the language practical and research-oriented

## 5. Example command flow

```powershell
git add .
git commit -m "Describe the release work"
git push origin main
gh release create vX.Y.Z --title "vX.Y.Z - Short release title" --notes-file release-notes.md
```
