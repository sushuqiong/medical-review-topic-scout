---
name: medical-review-topic-scout
description: Find and evaluate medical literature review topics from a disease-mechanism, disease-biomarker, disease-intervention, disease-exposure, or disease-omics pair. Use when the user asks for a review topic that has enough literature, is not already saturated, has limited direct competing reviews, or needs a Chinese-style "选题报告" with PubMed search counts, synonym/MeSH search strings, novelty assessment, gap evidence, recommended title, evidence support, duplicate-check conclusion, priority scoring, and backup directions.
---

# Medical Review Topic Scout

## Core Idea

Turn a vague pair such as "Alzheimer disease and gut microbiome" into a defensible medical review topic by mapping adjacent angles, measuring literature volume, checking recent direct reviews, and recommending a topic that is neither empty nor saturated.

Do not claim a topic has "never been written" unless reproducible searches show no direct reviews. Prefer calibrated labels: `严重饱和`, `饱和`, `近期有综述`, `刚被占`, `略窄`, `有空间`, or `空白`.

## Workflow

1. Parse the user's pair into:
   - Disease or clinical condition.
   - Element: mechanism, biomarker, omics layer, pathway, cell type, drug, intervention, exposure, phenotype, imaging feature, or population.
   - Intended article type: narrative review by default; scoping/systematic review only if requested.
2. Generate 8-12 candidate directions, from broad to narrow:
   - Broad field: `element x disease`.
   - Mechanistic sub-angles: pathway, cell type, metabolite, immune axis, organ axis, gene, omics, or clinical phenotype.
   - Translational angle: diagnosis, prognosis, therapy, adverse events, precision medicine.
   - Integrative angle: two complementary technologies or mechanisms.
3. Build concept blocks before searching. Within a block, use OR synonyms; between blocks, use AND. In `scripts/pubmed_topic_scan.py`, separate blocks with `|` and synonyms with `/`.
   - Disease block: `Alzheimer disease/Alzheimer's disease/mesh:Alzheimer Disease`
   - Element block: `gut microbiome/gut microbiota/intestinal microbiota/mesh:Gastrointestinal Microbiome`
   - Mechanism block: `tau/phosphorylated tau/neurofibrillary tangles`
4. Use `scripts/pubmed_topic_scan.py` for objective counts whenever internet is available:
   ```bash
   python scripts/pubmed_topic_scan.py --direction "gut microbiome/gut microbiota/mesh:Gastrointestinal Microbiome|Alzheimer disease/Alzheimer's disease/mesh:Alzheimer Disease" --direction "tau/phosphorylated tau|gut microbiome/gut microbiota|Alzheimer disease/Alzheimer's disease"
   ```
5. For each candidate, assess:
   - 5-year total count.
   - Total review count and recent review count.
   - Title-level recent review count as the strictest direct competition signal.
   - Most recent direct competing reviews and whether they are broad, disease-specific, mechanism-specific, or only tangential.
   - Presence of primary evidence sufficient to support mechanisms.
   - PubMed QueryTranslation, to detect mistranslated or over-expanded searches.
6. Pick one recommended topic and 2-4 backup directions. Prefer a mid-scope mechanism or translational angle, not the broadest keyword pair.

## Search Standards

Use PubMed first. Use web search only to verify ambiguous citations, journal details, or non-PubMed records.

Build queries with title/abstract terms plus MeSH where helpful. Avoid overfitting:

- Broad volume query: `(Disease synonyms) AND (Element synonyms)`.
- Direct review query: `(Disease synonyms) AND (Element synonyms) AND (review[Publication Type] OR systematic review[Publication Type] OR meta-analysis[Publication Type] OR review[Title])`.
- Strict competition query: all core concepts in `[Title]` plus review/meta-analysis filters.
- Narrow novelty query: include the exact proposed mechanism or angle.
- Recent competition query: restrict to the last 2-3 years and sort by publication date.

Always inspect PubMed `QueryTranslation` when available. If the translation expands a concept into irrelevant meanings, tighten the field tags or use exact phrases. If MeSH terms are missing for very new concepts, rely more on Title/Abstract terms.

For Chinese disease names, translate to English biomedical terms before searching. Include common synonyms and spelling variants: `Alzheimer disease` / `Alzheimer's disease`; `gut microbiome` / `gut microbiota` / `intestinal microbiota`; `tumor microenvironment` / `TME`.

For a serious manuscript topic, recommend confirming PubMed findings in at least one additional database:

- Web of Science or Scopus for citation and interdisciplinary coverage.
- Embase for biomedical/pharmacological coverage, if available.
- Google Scholar only as a broad sanity check, not as the primary count source.

## Saturation Heuristics

Use judgment, but start with these labels:

- `严重饱和`: multiple title-level recent direct reviews or many same-scope reviews in the last 12-24 months.
- `饱和`: more than 100 five-year papers and 5 or more direct reviews in the last 3 years.
- `近期有综述`: a directly overlapping review was published in the last 18 months.
- `刚被占`: exactly one direct review appeared very recently, especially if it has the same disease, element, and mechanism.
- `有空间`: enough primary literature, but direct reviews are absent, older, broad, or only tangential.
- `空白`: no direct reviews and at least 30-50 relevant recent papers or a strong adjacent literature base.
- `略窄`: fewer than 20-30 relevant recent papers unless adjacent mechanism literature can support the review.

Good review topics usually sit in the middle: not the broadest `disease x element`, but a mechanism or translational angle with enough primary evidence and incomplete review coverage.

## Gap Verification

Do not use a single count as proof of novelty. Create a short evidence package:

- Closest 3-5 reviews: title, year, PMID/DOI, scope, overlap score.
- Closest 3-5 original studies: title, year, PMID/DOI, why they support the proposed angle.
- Negative evidence: exact queries that did not find direct reviews.
- Difference statement: one sentence explaining what the proposed review covers that the closest review does not.

Use this overlap scoring:

| Overlap | Meaning | Action |
|---:|---|---|
| >80% | Same disease, same element, same mechanism and similar article scope | Do not recommend unless an update is clearly justified |
| 50-80% | Same field but different mechanism, population, method, or translational focus | Recommend only with explicit differentiation |
| <50% | Adjacent or broad review only | Usually acceptable |

## Priority Scoring

When comparing candidates, score each 0-100. The script reports a rough viability score; refine it manually:

| Criterion | Weight | What to reward |
|---|---:|---|
| Literature sufficiency | 30 | 30-180 recent papers, not too sparse or too huge |
| Competition safety | 25 | Few title-level recent direct reviews |
| Timeliness | 20 | Active growth in the last 2-3 years |
| Mechanistic coherence | 15 | Clear causal/pathway story, not a loose keyword bundle |
| Publication fit | 10 | Feasible narrative/scoping review for target journals |

## Report Format

Write the final answer in Chinese unless the user asks otherwise. Use this structure:

```markdown
# 综述选题报告：{元素} 与 {疾病}

## 一、前言
一句话说明该领域为什么值得写，以及本次如何判断选题空间。

### 相关领域全景俯瞰
| 方向 | 近5年总量 | 近期题名级竞争综述 | 可写性评分 | 判定 |
|---|---:|---:|---:|---|
| ... | ... | ... | ... | ... |

## 二、推荐选题
**建议标题：** English title

- **方向：** ...
- **核心检索式：** `...`
- **创新点：**
  1. ...
  2. ...
  3. ...

## 三、文献量支撑
- 近5年总命中：...
- 可延伸文献池：...
- 代表性原始研究/机制证据：...
- 代表性综述和空白：...

## 四、查重结论
- 直接竞争综述：...
- 最接近文献相似度：...
- 范围差异：...
- 结论：与拟写综述是否重叠、是否构成竞争、如何差异化。

## 五、推荐大纲
1. ...
2. ...
3. ...

## 六、检索日志
- PubMed 检索日期：...
- 核心检索式：...
- QueryTranslation：...
- 限制条件：...
- 需要补检数据库：...

## 七、备选方向
| 方向 | 状态 | 建议 |
|---|---|---|
| ... | ... | ... |

## 八、风险与下一步
- 风险：...
- 下一步：建议补检数据库、精读文献、确定目标期刊。
```

## Quality Bar

- Always include exact search strings and date windows.
- Distinguish all papers, all reviews, recent reviews, title-level direct reviews, and true direct competitors.
- Treat title-level recent reviews as stronger evidence of direct competition than broad title/abstract review hits.
- Cite PMIDs/DOIs when available for direct competitors and representative evidence.
- If counts come from live search, state the search date.
- If live search is unavailable, state that counts are estimates and provide reproducible queries for the user to run.
- Avoid inventing precise counts. Use the script, PubMed, or clearly mark estimates.
- Avoid recommending a topic solely because it has zero direct reviews; confirm that there is enough primary literature or adjacent evidence to write a real review.
- Do not overstate novelty. Use "可能存在空间", "直接竞争较少", or "需要进一步数据库补检确认" when appropriate.
- For clinical claims, avoid medical advice framing; this skill is for literature topic selection.

## Resources

- `scripts/pubmed_topic_scan.py`: PubMed count, direct-review, QueryTranslation, scoring, JSON/CSV scanner using NCBI E-utilities.
- `references/report-template.md`: Copyable Chinese report template.
