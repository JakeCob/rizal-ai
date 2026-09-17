/**
 * Behavior: grading is local and exact. Token exercises compare the picked
 * sequence to the answer sequence; multiple choice compares the index.
 */
import { describe, expect, it } from "vitest";
import { grade } from "./grade";
import { MOCK_LESSON } from "@/lib/api/fixtures";

const [assembly, translate, listen, mc] = MOCK_LESSON.exercises.map((e) => e.exercise);

describe("grade", () => {
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

  it("grades comprehension_mc by option index", () => {
    expect(grade(mc, { optionIndex: 0 })).toBe(true);
    expect(grade(mc, { optionIndex: 1 })).toBe(false);
  });

  it("treats a mismatched response shape as wrong", () => {
    expect(grade(mc, { tokens: ["x"] })).toBe(false);
    expect(grade(assembly, { optionIndex: 0 })).toBe(false);
  });
});
