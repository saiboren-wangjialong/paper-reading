# paper-reading

Automated daily paper discovery and bilingual abstract generation.

## Paper Daily

This repository includes a GitHub Actions workflow that runs every day to:

1. Query arXiv papers by your configured topic keywords
2. Generate English + Chinese abstracts for each paper
3. Save the result to `daily-papers.md`

### 1) Configure your topic

Edit `paper_daily_config.json`:

- `query`: your major/topic keywords (arXiv query syntax)
- `max_results`: number of papers per run

### 2) Configure translation (required for Chinese abstracts)

In repository settings, add:

- `OPENAI_API_KEY` (Actions secret)
- Optional `OPENAI_BASE_URL` (Actions variable, for custom OpenAI-compatible endpoint)
- Optional `OPENAI_MODEL` (Actions variable, default: `gpt-4o-mini`)

If `OPENAI_API_KEY` is not configured, the workflow still runs and keeps Chinese summary as fallback text.

### 3) Run

- Daily schedule: defined in `.github/workflows/paper-daily.yml`
- Manual run: Actions -> **Paper Daily** -> **Run workflow**
