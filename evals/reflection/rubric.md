# Reflection eval rubric

Blind grading of the "In Rizal's voice" reflection across models (DECISIONS.md D09, D32). The harness writes one sample per model per lesson with the model name hidden; grade every sample on the five criteria below, then reveal the key.

Score each criterion 0, 1, or 2. A sample with any 0 on criteria 1 or 2 fails regardless of total.

1. Tagalog naturalness. 2: reads as spoken modern Tagalog, nothing a Manila speaker would flag. 1: understandable but a phrase or two is translated English. 0: reads as translated English throughout.
2. Faithfulness. 2: every claim about the scene is in the cited passages. 1: a harmless embellishment. 0: invents an event, date, letter, or feeling not in the passages.
3. Voice. 2: reflective, wry, affectionate toward the country, not preachy. 1: flat but in character. 0: generic motivational tone or lecturing.
4. Quotation use. 2: quotes verbatim and to the point, or quotes nothing when nothing fits. 1: quotes verbatim but the quote adds little. 0: misquotes (the validator would already have rejected this).
5. English rendering. 2: says the same thing as the Tagalog, in natural English. 1: drifts in meaning. 0: contradicts the Tagalog.

Record scores in the results folder's `scores.csv` as `sample_id,c1,c2,c3,c4,c5,notes`. The harness joins scores with the key to produce the per-model summary.

Cost and latency are recorded per sample by the harness; they are context for the decision, not criteria.
