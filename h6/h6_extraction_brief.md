# H6 extraction brief (frozen 23 October 2026, before extraction)

You are one of two independent extractors for a systematic review. Read the protocol at /root/analysis/h6/h6_protocol.md (Eligibility and Extraction sections). Your list of studies is the file named in your instructions. For each study, open the full text (fulltext_url, or another open version you find) and extract every comparison of a treatment with a control that fits the study's stratum.

Rules:
- Record numbers exactly as reported. Do not compute effect sizes, convert units, or estimate values from figures unless the paper gives no numbers. If you must read a figure, set "from_figure": true.
- One record per comparison per outcome. If an experiment has several treatment arms, record each arm against the control. If it has several outcomes, record each one, and mark which one the authors call primary.
- The direction must be clear: "higher_is_more_prosocial": true or false.
- Quote the sentence or table cell each number comes from, at most 30 words, and give its location (page, table or figure).
- If the full text cannot be opened, write one record with "accessible": false and leave the numbers empty.
- Do not open any file under /root/analysis except the protocol, this brief and your study list. Use WebSearch and WebFetch. Do not use the browser.

Output: a JSON list written to the output file named in your instructions. Each record has these keys:
- study_id, citation, experiment, arm_label, accessible;
- design (between or within), population (children or adults), country, weird (true if the sample is from Western, educated, industrialized, rich, democratic countries; false otherwise);
- treatment_description, control_description;
- narrative_type: traditional_religious, traditional_folk, modern_invented or non_narrative;
- target: stranger, ingroup or unclear;
- delay: immediate or delayed (record the delay if delayed);
- outcome_description, incentivized (true or false), primary_outcome (true or false), higher_is_more_prosocial;
- stat_type: means_sd, means_se, t, F1, chi2_1df, proportions, regression, d_reported or other;
- values: an object with the numbers for that stat type:
  - means_sd: m_t, sd_t, n_t, m_c, sd_c, n_c;
  - means_se: m_t, se_t, n_t, m_c, se_c, n_c;
  - t: t, n_t, n_c;
  - F1: F, n_t, n_c;
  - chi2_1df: chi2, n_t, n_c;
  - proportions: p_t, n_t, p_c, n_c;
  - regression: b, se, sd_y, n_t, n_c;
  - d_reported: d, n_t, n_c;
  - other: free text;
- quote, location, from_figure, preregistered (Y, N or unknown), notes.

Final reply: the number of studies opened, the number of records, and any study you could not extract and why.
