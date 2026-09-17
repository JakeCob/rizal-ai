/** Mock reflection for the placeholder lesson. The quoted span is a verbatim
 * substring of the Spanish passage below, as the validator would require. */
import type { CompleteOut, ReflectionOut } from "@/lib/types.generated";
import { LESSON_ID } from "./fixtures";

export const ES_PASSAGE_ID = "aa000000-0000-4000-8000-000000000001";
export const TL_PASSAGE_ID = "aa000000-0000-4000-8000-000000000002";
export const EN_PASSAGE_ID = "aa000000-0000-4000-8000-000000000003";

export const MOCK_REFLECTION: ReflectionOut = {
  lesson_id: LESSON_ID,
  status: "published",
  model: "fake",
  prompt_version: "v1",
  layers: [
    {
      language: "es",
      translator: null,
      label: "Spanish (Rizal's original, 1887)",
      passages: [
        {
          id: ES_PASSAGE_ID,
          chapter: 1,
          paragraph_index: 1,
          text: "A fines de Octubre, don Santiago de los Santos, conocido popularmente con el nombre de «Capitán Tiago», daba una cena.",
        },
      ],
    },
    {
      language: "tl",
      translator: "poblete_1909",
      label: "Tagalog (Pascual Poblete's 1909 translation)",
      passages: [
        {
          id: TL_PASSAGE_ID,
          chapter: 1,
          paragraph_index: 1,
          text: "Nag-anyaya n~g pagpapacain nang isáng hapunan, n~g magtátapos ang Octubre, si Guinoong Santiago de los Santos.",
        },
      ],
    },
    {
      language: "en",
      translator: "derbyshire_1912",
      label: "English (Charles Derbyshire's 1912 translation)",
      passages: [
        {
          id: EN_PASSAGE_ID,
          chapter: 1,
          paragraph_index: 1,
          text: "On the last of October Don Santiago de los Santos, popularly known as Capitan Tiago, gave a dinner.",
        },
      ],
    },
  ],
  reflection: {
    tl: "Isang hapunan lang iyon sa Binondo, pero doon ko unang nakita kung paano nagtitipon ang aking bayan. Sinulat ko noon na si Kapitan Tiago ay \"daba una cena\", at sa likod ng mga salitang iyon ay ang buong Maynila.",
    en: "It was only a dinner in Binondo, but there I first saw how my country gathers. I wrote then that Capitan Tiago \"daba una cena\", and behind those words was all of Manila.",
    quoted_spans: [{ text: "daba una cena", passage_id: ES_PASSAGE_ID }],
  },
};

export const MOCK_REFLECTION_FALLBACK: ReflectionOut = {
  ...MOCK_REFLECTION,
  status: "fallback",
  reflection: null,
};

export function mockComplete(lessonId: string, results: { exerciseId: string; correct: boolean }[]): CompleteOut {
  const xp = results.filter((r) => r.correct).length * 10;
  return {
    lesson_id: lessonId,
    xp_earned: xp,
    total_xp: xp,
    streak_count: 1,
    hearts: 5 - results.filter((r) => !r.correct).length,
    results: results.map((r) => ({ exercise_id: r.exerciseId, correct: r.correct, xp: r.correct ? 10 : 0 })),
  };
}
