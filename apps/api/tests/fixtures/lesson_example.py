"""A minimal valid lesson in the content YAML shape. Placeholder text only;
this is scaffolding, not authored content."""

LESSON_EXAMPLE: dict = {
    "slug": "scaffold-placeholder",
    "title": "Scaffold placeholder lesson",
    "published": True,
    "estimated_minutes": 4,
    "grammar_focus": ["ay-inversion", "ng-marker"],
    "target_vocab": [
        {"tl": "dumating", "en": "arrived", "pos": "verb"},
        {"tl": "hapunan", "en": "dinner", "pos": "noun"},
        {"tl": "bisita", "en": "guest", "pos": "noun"},
    ],
    "source_passages": [
        {"work": "noli", "language": "es", "chapter": 1, "paragraph_index": 1},
        {"work": "noli", "language": "tl", "chapter": 1, "paragraph_index": 1},
    ],
    "vignette": [
        {
            "line_id": "b1",
            "speaker": None,
            "tl": "May hapunan sa bahay ni Kapitan Tiago.",
            "en": "There is a dinner at Capitan Tiago's house.",
        },
        {
            "line_id": "b2",
            "speaker": "Tiya Isabel",
            "tl": "Marami ang bisita ngayong gabi.",
            "en": "There are many guests tonight.",
            "exercise_after": "ex1",
        },
        {"line_id": "b3", "speaker": None, "tl": "Dumating ang isang binata.", "en": "A young man arrived."},
        {
            "line_id": "b4",
            "speaker": "Kapitan Tiago",
            "tl": "Siya si Crisostomo Ibarra.",
            "en": "This is Crisostomo Ibarra.",
        },
    ],
    "exercises": [
        {
            "type": "sentence_assembly",
            "key": "ex1",
            "prompt_en": "There are many guests tonight.",
            "answer_tokens": ["Marami", "ang", "bisita", "ngayong", "gabi"],
            "bank": ["Marami", "ang", "bisita", "ngayong", "gabi", "kahapon", "kaunti"],
        },
        {
            "type": "translate_line",
            "key": "ex2",
            "direction": "tl_to_en",
            "prompt": "Dumating ang isang binata.",
            "answer_tokens": ["A", "young", "man", "arrived"],
            "bank": ["A", "young", "man", "arrived", "left", "woman"],
        },
        {
            "type": "listen_tap",
            "key": "ex3",
            "audio_url": None,
            "transcript_tl": "Siya si Crisostomo Ibarra.",
            "answer_tokens": ["Siya", "si", "Crisostomo", "Ibarra"],
            "bank": ["Siya", "si", "Crisostomo", "Ibarra", "sila", "ni"],
        },
        {
            "type": "comprehension_mc",
            "key": "ex4",
            "question": "Where is the dinner held?",
            "options": ["At Capitan Tiago's house", "At the church", "On the ship"],
            "correct_index": 0,
            "explanation": "The first line says: sa bahay ni Kapitan Tiago.",
        },
        {
            "type": "sentence_assembly",
            "key": "ex5",
            "prompt_en": "A young man arrived.",
            "answer_tokens": ["Dumating", "ang", "isang", "binata"],
            "bank": ["Dumating", "ang", "isang", "binata", "dalaga", "umalis"],
        },
        {
            "type": "comprehension_mc",
            "key": "ex6",
            "question": "Who introduces Ibarra?",
            "options": ["Tiya Isabel", "Kapitan Tiago", "Padre Damaso", "Maria Clara"],
            "correct_index": 1,
            "explanation": None,
        },
    ],
}
