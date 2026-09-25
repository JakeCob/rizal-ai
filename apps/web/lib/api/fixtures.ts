/**
 * Mock data mirroring content/units/01-noli-arrival. Used by the mock API
 * mode (NEXT_PUBLIC_API_MODE=mock), by unit tests, and by the Playwright
 * smoke test, so the web app can be developed and verified with no backend.
 */
import type { LessonOut, Tree, UserOut } from "@/lib/types.generated";

export const UNIT_ID = "7d8e1f2a-3b4c-5d6e-8f90-1a2b3c4d5e6f";
export const LESSON_ID = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d";

export const MOCK_TREE: Tree = {
  units: [
    {
      id: UNIT_ID,
      slug: "noli-arrival",
      title: "Noli Me Tangere: Ibarra's return",
      order_index: 1,
      lessons: [
        {
          id: LESSON_ID,
          slug: "scaffold-placeholder",
          title: "Placeholder: the dinner at Capitan Tiago's",
          order_index: 0,
          status: "active",
          xp_reward: 60,
          estimated_minutes: 4,
        },
        {
          id: "1b2c3d4e-5f60-4a7b-9c8d-0e1f2a3b4c5d",
          slug: "noli-ch02-placeholder",
          title: "Chapter 2: Crisostomo Ibarra",
          order_index: 1,
          status: "locked",
          xp_reward: 0,
          estimated_minutes: 5,
        },
        {
          id: "2c3d4e5f-6071-4b8c-ad9e-1f2a3b4c5d6e",
          slug: "noli-ch03-placeholder",
          title: "Chapter 3: The dinner",
          order_index: 2,
          status: "locked",
          xp_reward: 0,
          estimated_minutes: 5,
        },
        {
          id: "3d4e5f60-7182-4c9d-be0f-2a3b4c5d6e7f",
          slug: "noli-ch04-placeholder",
          title: "Chapter 4: Heretic and subversive",
          order_index: 3,
          status: "locked",
          xp_reward: 0,
          estimated_minutes: 5,
        },
      ],
    },
  ],
};

export const MOCK_LESSON: LessonOut = {
  id: LESSON_ID,
  unit_id: UNIT_ID,
  slug: "scaffold-placeholder",
  title: "Placeholder: the dinner at Capitan Tiago's",
  version: "mock",
  estimated_minutes: 4,
  grammar_focus: ["ay-inversion", "ng-marker"],
  target_vocab: [
    { tl: "dumating", en: "arrived", pos: "verb", note: null },
    { tl: "hapunan", en: "dinner", pos: "noun", note: null },
    { tl: "bisita", en: "guest", pos: "noun", note: null },
  ],
  source_passage_ids: [],
  vignette: [
    {
      line_id: "b1",
      speaker: null,
      tl: "May hapunan sa bahay ni Kapitan Tiago.",
      en: "There is a dinner at Capitan Tiago's house.",
      audio_url: null,
      exercise_after: null,
    },
    {
      line_id: "b2",
      speaker: "Tiya Isabel",
      tl: "Marami ang bisita ngayong gabi.",
      en: "There are many guests tonight.",
      audio_url: null,
      exercise_after: "ex1",
    },
    {
      line_id: "b3",
      speaker: null,
      tl: "Dumating ang isang binata.",
      en: "A young man arrived.",
      audio_url: null,
      exercise_after: null,
    },
    {
      line_id: "b4",
      speaker: "Kapitan Tiago",
      tl: "Siya si Crisostomo Ibarra.",
      en: "This is Crisostomo Ibarra.",
      audio_url: null,
      exercise_after: null,
    },
  ],
  exercises: [
    {
      id: "e1000000-0000-4000-8000-000000000001",
      order_index: 0,
      exercise: {
        type: "sentence_assembly",
        key: "ex1",
        xp: 10,
        prompt_en: "There are many guests tonight.",
        answer_tokens: ["Marami", "ang", "bisita", "ngayong", "gabi"],
        accepted_orders: [],
        bank: ["Marami", "ang", "bisita", "ngayong", "gabi", "kahapon", "kaunti"],
      },
    },
    {
      id: "e1000000-0000-4000-8000-000000000002",
      order_index: 1,
      exercise: {
        type: "translate_line",
        key: "ex2",
        xp: 10,
        direction: "tl_to_en",
        prompt: "Dumating ang isang binata.",
        answer_tokens: ["A", "young", "man", "arrived"],
        accepted_orders: [],
        bank: ["A", "young", "man", "arrived", "left", "woman"],
      },
    },
    {
      id: "e1000000-0000-4000-8000-000000000003",
      order_index: 2,
      exercise: {
        type: "listen_tap",
        key: "ex3",
        xp: 10,
        audio_url: null,
        transcript_tl: "Siya si Crisostomo Ibarra.",
        answer_tokens: ["Siya", "si", "Crisostomo", "Ibarra"],
        accepted_orders: [],
        bank: ["Siya", "si", "Crisostomo", "Ibarra", "sila", "ni"],
      },
    },
    {
      id: "e1000000-0000-4000-8000-000000000004",
      order_index: 3,
      exercise: {
        type: "comprehension_mc",
        key: "ex4",
        xp: 10,
        question: "Where is the dinner held?",
        options: ["At Capitan Tiago's house", "At the church", "On the ship"],
        correct_index: 0,
        explanation: "The first line says: sa bahay ni Kapitan Tiago.",
      },
    },
    {
      id: "e1000000-0000-4000-8000-000000000005",
      order_index: 4,
      exercise: {
        type: "sentence_assembly",
        key: "ex5",
        xp: 10,
        prompt_en: "A young man arrived.",
        answer_tokens: ["Dumating", "ang", "isang", "binata"],
        accepted_orders: [["isang", "binata", "ang", "Dumating"]],
        bank: ["Dumating", "ang", "isang", "binata", "dalaga", "umalis"],
      },
    },
    {
      id: "e1000000-0000-4000-8000-000000000006",
      order_index: 5,
      exercise: {
        type: "comprehension_mc",
        key: "ex6",
        xp: 10,
        question: "Who introduces Ibarra?",
        options: ["Tiya Isabel", "Kapitan Tiago", "Padre Damaso", "Maria Clara"],
        correct_index: 1,
        explanation: null,
      },
    },
  ],
};

export const MOCK_USER: UserOut = {
  id: "9f8e7d6c-5b4a-4392-8170-6f5e4d3c2b1a",
  timezone: "Asia/Manila",
  total_xp: 0,
  streak_count: 0,
  hearts: 5,
  last_activity_date: null,
};
