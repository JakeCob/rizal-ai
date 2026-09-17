/* Generated from packages/contracts/schema.json. Do not edit. */

export type AudioUrl = string | null;
export type En = string;
/**
 * Exercise key to run after this beat
 */
export type ExerciseAfter = string | null;
export type LineId = string;
export type Speaker = string | null;
export type Tl = string;
export type CorrectIndex = number;
export type Explanation = string | null;
/**
 * Stable key within the lesson
 */
export type Key = string;
/**
 * @minItems 2
 * @maxItems 4
 */
export type Options = [string, string] | [string, string, string] | [string, string, string, string];
export type Question = string;
export type Type = "comprehension_mc";
export type Xp = number;
export type Exercise = SentenceAssembly | TranslateLine | ListenTap | ComprehensionMC;
/**
 * @minItems 1
 */
export type AnswerTokens = [string, ...string[]];
/**
 * @minItems 1
 */
export type Bank = [string, ...string[]];
/**
 * Stable key within the lesson
 */
export type Key1 = string;
export type PromptEn = string;
export type Type1 = "sentence_assembly";
export type Xp1 = number;
/**
 * @minItems 1
 */
export type AnswerTokens1 = [string, ...string[]];
/**
 * @minItems 1
 */
export type Bank1 = [string, ...string[]];
export type Direction = "tl_to_en" | "en_to_tl";
/**
 * Stable key within the lesson
 */
export type Key2 = string;
export type Prompt = string;
export type Type2 = "translate_line";
export type Xp2 = number;
/**
 * @minItems 1
 */
export type AnswerTokens2 = [string, ...string[]];
export type AudioUrl1 = string | null;
/**
 * @minItems 1
 */
export type Bank2 = [string, ...string[]];
/**
 * Stable key within the lesson
 */
export type Key3 = string;
export type TranscriptTl = string;
export type Type3 = "listen_tap";
export type Xp3 = number;
export type Id = string;
export type OrderIndex = number;
export type EstimatedMinutes = number;
export type Exercises = ExerciseOut[];
export type GrammarFocus = string[];
export type Id1 = string;
export type Slug = string;
export type SourcePassageIds = string[];
export type En1 = string;
export type Note = string | null;
export type Pos = string | null;
export type Tl1 = string;
export type TargetVocab = VocabItem[];
export type Title = string;
export type UnitId = string;
export type Version = string;
export type Vignette = Beat[];
export type Id2 = string;
export type EstimatedMinutes1 = number;
export type Id3 = string;
export type OrderIndex1 = number;
export type Slug1 = string;
export type Status = "locked" | "active" | "done";
export type Title1 = string;
export type XpReward = number;
export type Lessons = TreeLesson[];
export type OrderIndex2 = number;
export type Slug2 = string;
export type Title2 = string;
export type Units = TreeUnit[];
export type Hearts = number;
export type Id4 = string;
export type LastActivityDate = string | null;
export type StreakCount = number;
export type Timezone = string;
export type TotalXp = number;

export interface RizalAIAPIContracts {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "Beat".
 */
export interface Beat {
  audio_url: AudioUrl;
  en: En;
  exercise_after: ExerciseAfter;
  line_id: LineId;
  speaker: Speaker;
  tl: Tl;
}
/**
 * Multiple choice about the passage.
 *
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ComprehensionMC".
 */
export interface ComprehensionMC {
  correct_index: CorrectIndex;
  explanation: Explanation;
  key: Key;
  options: Options;
  question: Question;
  type: Type;
  xp: Xp;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ExerciseOut".
 */
export interface ExerciseOut {
  exercise: Exercise;
  id: Id;
  order_index: OrderIndex;
}
/**
 * Build the Tagalog line from a word bank, given the English.
 *
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "SentenceAssembly".
 */
export interface SentenceAssembly {
  answer_tokens: AnswerTokens;
  bank: Bank;
  key: Key1;
  prompt_en: PromptEn;
  type: Type1;
  xp: Xp1;
}
/**
 * Translate a line in either direction from a word bank.
 *
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "TranslateLine".
 */
export interface TranslateLine {
  answer_tokens: AnswerTokens1;
  bank: Bank1;
  direction: Direction;
  key: Key2;
  prompt: Prompt;
  type: Type2;
  xp: Xp2;
}
/**
 * Hear a Tagalog line, tap the words heard.
 *
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ListenTap".
 */
export interface ListenTap {
  answer_tokens: AnswerTokens2;
  audio_url: AudioUrl1;
  bank: Bank2;
  key: Key3;
  transcript_tl: TranscriptTl;
  type: Type3;
  xp: Xp3;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "LessonOut".
 */
export interface LessonOut {
  estimated_minutes: EstimatedMinutes;
  exercises: Exercises;
  grammar_focus: GrammarFocus;
  id: Id1;
  slug: Slug;
  source_passage_ids: SourcePassageIds;
  target_vocab: TargetVocab;
  title: Title;
  unit_id: UnitId;
  version: Version;
  vignette: Vignette;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "VocabItem".
 */
export interface VocabItem {
  en: En1;
  note: Note;
  pos: Pos;
  tl: Tl1;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "Tree".
 */
export interface Tree {
  units: Units;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "TreeUnit".
 */
export interface TreeUnit {
  id: Id2;
  lessons: Lessons;
  order_index: OrderIndex2;
  slug: Slug2;
  title: Title2;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "TreeLesson".
 */
export interface TreeLesson {
  estimated_minutes: EstimatedMinutes1;
  id: Id3;
  order_index: OrderIndex1;
  slug: Slug1;
  status: Status;
  title: Title1;
  xp_reward: XpReward;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "UserOut".
 */
export interface UserOut {
  hearts: Hearts;
  id: Id4;
  last_activity_date: LastActivityDate;
  streak_count: StreakCount;
  timezone: Timezone;
  total_xp: TotalXp;
}
