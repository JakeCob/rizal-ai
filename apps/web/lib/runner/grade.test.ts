/**
 * Behavior: grading is local (DECISIONS.md D15, D34). A token exercise is
 * correct when the picked sequence equals answer_tokens or any listed
 * accepted order, ignoring letter case; multiple choice compares the index.
 * The token cases come from packages/contracts/grading-cases.json, the same
 * table the API grader is tested against, so the two cannot drift.
 */
import { describe, expect, it } from "vitest";
import { correctAnswerText, grade } from "./grade";
import { MOCK_LESSON } from "@/lib/api/fixtures";
import type { Exercise } from "@/lib/types.generated";
import gradingCases from "../../../../packages/contracts/grading-cases.json";

type GradingCase = {
  name: string;
  type: "sentence_assembly" | "translate_line" | "listen_tap";
  answer_tokens: string[];
  accepted_orders: string[][];
  tokens: string[];
  correct: boolean;
};

const CASES = gradingCases as GradingCase[];

/** A minimal exercise of the case's type; grading reads only the token fields. */
function exerciseFor(c: GradingCase): Exercise {
  const answer = c.answer_tokens as [string, ...string[]];
  const tokens = { answer_tokens: answer, accepted_orders: c.accepted_orders, bank: answer };
  switch (c.type) {
    case "sentence_assembly":
      return { type: c.type, key: "case", xp: 10, prompt_en: c.name, ...tokens };
    case "translate_line":
      return { type: c.type, key: "case", xp: 10, direction: "tl_to_en", prompt: c.name, ...tokens };
    case "listen_tap":
      return { type: c.type, key: "case", xp: 10, audio_url: null, transcript_tl: c.name, ...tokens };
  }
}

const [assembly, translate, listen, mc] = MOCK_LESSON.exercises.map((e) => e.exercise);

describe("grade, shared case table", () => {
  it("covers every token type", () => {
    expect(new Set(CASES.map((c) => c.type))).toEqual(
      new Set(["sentence_assembly", "translate_line", "listen_tap"]),
    );
  });

  it.each(CASES.map((c) => [c.name, c] as const))("%s", (_name, c) => {
    expect(grade(exerciseFor(c), { tokens: c.tokens })).toBe(c.correct);
  });
});

describe("grade, mock lesson", () => {
  it("accepts the exact token sequence for sentence_assembly", () => {
    expect(grade(assembly, { tokens: ["Marami", "ang", "bisita", "ngayong", "gabi"] })).toBe(true);
  });

  it("rejects a reordered token sequence", () => {
    expect(grade(assembly, { tokens: ["ang", "Marami", "bisita", "ngayong", "gabi"] })).toBe(false);
  });

  it("rejects a partial sequence", () => {
    expect(grade(assembly, { tokens: ["Marami", "ang"] })).toBe(false);
  });

  it("grades translate_line and listen_tap by tokens too", () => {
    expect(grade(translate, { tokens: ["A", "young", "man", "arrived"] })).toBe(true);
    expect(grade(listen, { tokens: ["Siya", "si", "Crisostomo", "Ibarra"] })).toBe(true);
    expect(grade(listen, { tokens: ["Sila", "si", "Crisostomo", "Ibarra"] })).toBe(false);
  });

  it("accepts the listed alternate order on the mock lesson", () => {
    const ex5 = MOCK_LESSON.exercises[4].exercise;
    expect(grade(ex5, { tokens: ["Isang", "binata", "ang", "dumating"] })).toBe(true);
  });

  it("grades comprehension_mc by option index", () => {
    expect(grade(mc, { optionIndex: 0 })).toBe(true);
    expect(grade(mc, { optionIndex: 1 })).toBe(false);
  });

  it("treats a mismatched response shape as wrong", () => {
    expect(grade(mc, { tokens: ["x"] })).toBe(false);
    expect(grade(assembly, { optionIndex: 0 })).toBe(false);
  });
});

describe("grade, malformed stored data", () => {
  const base = exerciseFor(CASES.find((c) => c.name === "case-only difference, sentence_assembly")!);
  const answer = ["Dumating", "ang", "isang", "binata"];

  it("grades on answer_tokens when accepted_orders is missing", () => {
    const legacy: Record<string, unknown> = { ...base };
    delete legacy.accepted_orders;
    const old = legacy as unknown as Exercise;
    expect(grade(old, { tokens: ["dumating", "ang", "isang", "binata"] })).toBe(true);
    expect(grade(old, { tokens: ["isang", "binata", "ang", "Dumating"] })).toBe(false);
  });

  it("grades a non-string token wrong instead of throwing", () => {
    const tokens = ["Dumating", "ang", 3, "binata"] as unknown as string[];
    expect(() => grade(base, { tokens })).not.toThrow();
    expect(grade(base, { tokens })).toBe(false);
  });

  it("ignores a non-array accepted_orders and skips non-array entries", () => {
    const notArray = { ...base, accepted_orders: "oops" } as unknown as Exercise;
    expect(grade(notArray, { tokens: answer })).toBe(true);
    expect(grade(notArray, { tokens: ["o", "o", "p", "s"] })).toBe(false);
    const badEntry = { ...base, accepted_orders: [null, "x", ["isang", "binata", "ang", "Dumating"]] } as unknown as Exercise;
    expect(() => grade(badEntry, { tokens: ["isang", "binata", "ang", "dumating"] })).not.toThrow();
    expect(grade(badEntry, { tokens: ["isang", "binata", "ang", "dumating"] })).toBe(true);
  });
});

describe("correctAnswerText", () => {
  it("joins answer_tokens, never an accepted order", () => {
    const c = CASES.find((x) => x.accepted_orders.length > 0);
    expect(c).toBeDefined();
    expect(correctAnswerText(exerciseFor(c!))).toBe(c!.answer_tokens.join(" "));
    expect(correctAnswerText(MOCK_LESSON.exercises[4].exercise)).toBe("Dumating ang isang binata");
  });
});
