# medical-review-topic-scout

Local Codex skill for scouting biomedical review topics from a disease-mechanism,
disease-biomarker, disease-intervention, disease-exposure, or disease-omics pair.

## Contents

- `SKILL.md` - Codex skill instructions and report workflow.
- `scripts/pubmed_topic_scan.py` - PubMed E-utilities scanner for counts,
  direct-review checks, QueryTranslation capture, viability scoring, JSON/CSV
  export, synonym blocks, and MeSH terms.
- `references/report-template.md` - Chinese topic report template.
- `agents/openai.yaml` - UI metadata.

## Quick Test

```powershell
python .\scripts\pubmed_topic_scan.py --direction "gut microbiome/gut microbiota/mesh:Gastrointestinal Microbiome|Alzheimer disease/Alzheimer's disease/mesh:Alzheimer Disease"
```

## Invocation Example

```text
Use $medical-review-topic-scout 我想写一篇 胃癌 和 肿瘤相关成纤维细胞 相关的综述，帮我找个文献量够、直接竞争少的选题。
```
