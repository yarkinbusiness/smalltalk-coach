# Vision extraction evaluation

This harness compares local chat-screenshot cases with transcript extraction.
Run the committed synthetic checks without a network call or API key:

```sh
backend/.venv/bin/python -m backend.eval.vision_eval --cases backend/eval/vision_cases/synthetic --mock
```

For a live run, put each image and its `<case_id>.expected.json` sidecar in
`backend/eval/vision_cases/real/`, then run:

```sh
SMALLTALK_VISION_EVAL=1 ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  backend/.venv/bin/python -m backend.eval.vision_eval \
  --cases backend/eval/vision_cases/real --out vision-eval-report.json
```

The sidecar must identify its image, image media type, declared user-message
side (`left`, `right`, or `unknown`), and expected turns. Unknown-side cases
must label every expected turn as `other`. Copy the shape in the synthetic
fixtures. Reports omit transcript text by default; use `--include-text` only
for a securely handled local report.

Before adding a real case, the founder must confirm all of the following:

- Written consent from both conversation parties, or crop/redact the other
  party's name and avatar.
- No minors and no sensitive-category content.
- Images remain local, are never committed, and stay under the gitignored
  `real/` directory.
- The only transmission is the single Anthropic API call made by this eval;
  provide the API key through the environment only.

The recorded pass thresholds are recall at least 0.95, fidelity at least 0.90,
order exactly 1.0, and attribution exactly 1.0. Recall is the share of expected
turns found; fidelity is average text similarity for matched turns; order checks
matched-turn sequence; attribution checks the matched speaker labels. Thresholds
can be changed with the four `--*-threshold` flags. Per COACHING_PIPELINE_V1
section 6, manually inspect every failed case before any model-pin decision.
