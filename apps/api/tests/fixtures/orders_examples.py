"""Token exercises for the orders helper tests (plan 006), copied from the
lesson files on 2026-09-25 so that re-authoring a lesson cannot break the
helper's tests. Each constant names the lesson and key it came from; the
values are frozen here on purpose and are not kept in sync."""

# 01-ibarra-arrival.yaml ex5
L1_EX5: dict = {
    "type": "listen_tap",
    "key": "ex5",
    "audio_url": None,
    "transcript_tl": "Salamat po sa inyong papuri sa aking ama.",
    "answer_tokens": ["Salamat", "po", "sa", "inyong", "papuri", "sa", "aking", "ama"],
    "bank": ["Salamat", "po", "sa", "inyong", "papuri", "sa", "aking", "ama", "ina", "iyong"],
}

# 01-ibarra-arrival.yaml ex7
L1_EX7: dict = {
    "type": "sentence_assembly",
    "key": "ex7",
    "prompt_en": "Tomorrow I leave for San Diego.",
    "answer_tokens": ["Bukas", "ay", "aalis", "ako", "patungong", "San", "Diego"],
    "accepted_orders": [
        ["Bukas", "aalis", "ako", "patungong", "San", "Diego"],
        ["aalis", "ako", "Bukas", "patungong", "San", "Diego"],
        ["aalis", "ako", "patungong", "San", "Diego", "Bukas"],
        ["Bukas", "ako", "aalis", "patungong", "San", "Diego"],
    ],
    "bank": ["Bukas", "ay", "aalis", "ako", "patungong", "San", "Diego", "dumating", "kami"],
}

# 02-the-dinner.yaml ex3
L2_EX3: dict = {
    "type": "sentence_assembly",
    "key": "ex3",
    "prompt_en": "Padre Damaso ended up with the neck and the wing of the chicken.",
    "answer_tokens": ["Napunta", "kay", "Padre", "Damaso", "ang", "leeg", "at", "pakpak", "ng", "manok"],
    "accepted_orders": [
        ["Napunta", "ang", "leeg", "at", "pakpak", "ng", "manok", "kay", "Padre", "Damaso"],
        ["kay", "Padre", "Damaso", "Napunta", "ang", "leeg", "at", "pakpak", "ng", "manok"],
    ],
    "bank": [
        "Napunta",
        "kay",
        "Padre",
        "Damaso",
        "ang",
        "leeg",
        "at",
        "pakpak",
        "ng",
        "manok",
        "si",
        "hita",
        "ni",
    ],
}

# 02-the-dinner.yaml ex4
L2_EX4: dict = {
    "type": "listen_tap",
    "key": "ex4",
    "audio_url": None,
    "transcript_tl": "Galit na galit siya pero hindi siya nagsalita.",
    "answer_tokens": ["Galit", "na", "galit", "siya", "pero", "hindi", "siya", "nagsalita"],
    "bank": [
        "Galit",
        "na",
        "galit",
        "siya",
        "pero",
        "hindi",
        "siya",
        "nagsalita",
        "masaya",
        "kami",
        "sumigaw",
    ],
}

# 02-the-dinner.yaml ex6
L2_EX6: dict = {
    "type": "translate_line",
    "key": "ex6",
    "direction": "en_to_tl",
    "prompt": "Ever since I was a child.",
    "answer_tokens": ["Mula", "noong", "bata", "pa", "ako"],
    "accepted_orders": [["Mula", "pa", "noong", "bata", "ako"], ["Mula", "noong", "bata", "ako"]],
    "bank": ["Mula", "noong", "bata", "pa", "ako", "ka", "ngayon", "matanda"],
}

# 03-heretic-filibuster.yaml ex2
L3_EX2: dict = {
    "type": "sentence_assembly",
    "key": "ex2",
    "prompt_en": "How did my father die? (politely, to an elder)",
    "answer_tokens": ["Paano", "po", "namatay", "ang", "aking", "ama"],
    "accepted_orders": [["Paano", "po", "ba", "namatay", "ang", "aking", "ama"]],
    "bank": ["Paano", "po", "namatay", "ang", "aking", "ama", "ina", "nabuhay", "saan", "ba"],
}

# 04-azotea.yaml ex8
L4_EX8: dict = {
    "type": "sentence_assembly",
    "key": "ex8",
    "prompt_en": "Okay, I'll read it to you now.",
    "answer_tokens": ["Sige", "basahin", "ko", "na", "sa", "iyo"],
    "accepted_orders": [["Sige", "na", "basahin", "ko", "sa", "iyo"]],
    "bank": ["Sige", "basahin", "ko", "na", "sa", "iyo", "binasa", "sulat", "niya"],
}

# 01-the-town.yaml ex4
L5_EX4: dict = {
    "type": "translate_line",
    "key": "ex4",
    "direction": "tl_to_en",
    "prompt": "Mula noon, wala nang lumalapit sa puno.",
    "answer_tokens": ["From", "then", "on", "nobody", "went", "near", "the", "tree"],
    "accepted_orders": [["nobody", "went", "near", "the", "tree", "From", "then", "on"]],
    "bank": ["From", "then", "on", "nobody", "went", "near", "the", "tree", "everyone", "river", "sold"],
}

# 01-the-town.yaml ex8
L5_EX8: dict = {
    "type": "translate_line",
    "key": "ex8",
    "direction": "en_to_tl",
    "prompt": "The old man is here!",
    "answer_tokens": ["Nandiyan", "na", "ang", "matanda"],
    "accepted_orders": [["ang", "matanda", "Nandiyan", "na"]],
    "bank": ["Nandiyan", "na", "ang", "matanda", "bayabas", "puno", "takbo"],
}

# 01-the-town.yaml ex2
L5_EX2: dict = {
    "type": "sentence_assembly",
    "key": "ex2",
    "prompt_en": "The whole town respects it.",
    "answer_tokens": ["Iginagalang", "ito", "ng", "buong", "bayan"],
    "accepted_orders": [["Iginagalang", "ng", "buong", "bayan", "ito"]],
    "bank": ["Iginagalang", "ito", "ng", "buong", "bayan", "nila", "lawa", "gubat"],
}

# 01-the-town.yaml ex1
L5_EX1: dict = {
    "type": "comprehension_mc",
    "key": "ex1",
    "question": "Where is the town of San Diego?",
    "options": ["Near the lake", "By the sea", "In the mountains", "In Manila"],
    "correct_index": 0,
    "explanation": "Malapit sa lawa ang bayan ng San Diego (the town of San Diego lies near the lake).",
}

# Probes from the review, not from any lesson.
BANK_PROBE: dict = {
    "type": "sentence_assembly",
    "key": "probe1",
    "prompt_en": "He has left.",
    "answer_tokens": ["Umalis", "na", "siya"],
    "bank": ["Umalis", "na", "siya", "po"],
}
# Two copies of the block "na X" can join with a lone "na" into the same order,
# so the closed form overcounts in block mode.
BLOCK_OVERCOUNT_PROBE: dict = {
    "type": "sentence_assembly",
    "key": "probe2",
    "prompt_en": "Probe.",
    "answer_tokens": ["na", "na", "X", "na"],
    "bank": ["na", "na", "X", "na"],
}
