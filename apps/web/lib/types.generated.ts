/* Generated from packages/contracts/schema.json. Do not edit. */

/**
 * The client's local grade; recorded but not trusted
 */
export type Correct = boolean;
export type DurationMs = number;
export type ExerciseId = string;
export type Correct1 = boolean;
export type Hearts = number;
export type AudioUrl = string | null;
export type En = string;
/**
 * Exercise key to run after this beat
 */
export type ExerciseAfter = string | null;
export type LineId = string;
export type Speaker = string | null;
export type Tl = string;
export type Hearts1 = number;
export type LessonId = string;
export type Correct2 = boolean;
export type ExerciseId1 = string;
export type Xp = number;
export type Results = ResultOut[];
export type StreakCount = number;
export type TotalXp = number;
export type XpEarned = number;
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
export type Xp1 = number;
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
export type Xp2 = number;
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
export type Xp3 = number;
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
export type Xp4 = number;
export type Id = string;
export type OrderIndex = number;
export type Label = string;
export type Language = "es" | "tl" | "en";
export type Chapter = number;
export type Id1 = string;
export type ParagraphIndex = number;
export type Text = string;
export type Passages = PassageOut[];
export type Translator = string | null;
export type EstimatedMinutes = number;
export type Exercises = ExerciseOut[];
export type GrammarFocus = string[];
export type Id2 = string;
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
export type PassageId = string;
export type Text1 = string;
/**
 * English rendering of the Tagalog reflection
 */
export type En2 = string;
export type QuotedSpans = QuotedSpan[];
/**
 * Reflection in modern Tagalog, in Rizal's voice
 */
export type Tl2 = string;
export type Layers = LayerOut[];
export type LessonId1 = string;
export type Model = string;
export type PromptVersion = string;
export type Status = "published" | "fallback";
export type DurationMs1 = number;
export type ExerciseId2 = string;
export type Correct3 = boolean;
export type Hearts2 = number;
export type NextDueAt = string;
export type SessionAnswered = number;
export type State = string;
export type DueAt = string;
export type Reps = number;
export type State1 = string;
export type Items = ReviewItemOut[];
export type Id3 = string;
export type EstimatedMinutes1 = number;
export type Id4 = string;
export type OrderIndex1 = number;
export type Slug1 = string;
export type Status1 = "locked" | "active" | "done";
export type Title1 = string;
export type XpReward = number;
export type Lessons = TreeLesson[];
export type OrderIndex2 = number;
export type Slug2 = string;
export type Title2 = string;
export type Units = TreeUnit[];
export type Hearts3 = number;
export type Id5 = string;
export type LastActivityDate = string | null;
export type StreakCount1 = number;
export type Timezone = string;
export type TotalXp1 = number;

export interface RizalAIAPIContracts {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "AttemptIn".
 */
export interface AttemptIn {
  correct: Correct;
  duration_ms: DurationMs;
  exercise_id: ExerciseId;
  response: Response;
}
export interface Response {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "AttemptOut".
 */
export interface AttemptOut {
  correct: Correct1;
  hearts: Hearts;
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
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "CompleteOut".
 */
export interface CompleteOut {
  hearts: Hearts1;
  lesson_id: LessonId;
  results: Results;
  streak_count: StreakCount;
  total_xp: TotalXp;
  xp_earned: XpEarned;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ResultOut".
 */
export interface ResultOut {
  correct: Correct2;
  exercise_id: ExerciseId1;
  xp: Xp;
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
  xp: Xp1;
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
  xp: Xp2;
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
  xp: Xp3;
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
  xp: Xp4;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "LayerOut".
 */
export interface LayerOut {
  label: Label;
  language: Language;
  passages: Passages;
  translator: Translator;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "PassageOut".
 */
export interface PassageOut {
  chapter: Chapter;
  id: Id1;
  paragraph_index: ParagraphIndex;
  text: Text;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "LessonOut".
 */
export interface LessonOut {
  estimated_minutes: EstimatedMinutes;
  exercises: Exercises;
  grammar_focus: GrammarFocus;
  id: Id2;
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
 * A span of the reflection that carries Rizal's byline. Must be a
 * verbatim substring of the cited passage (DECISIONS.md D03).
 *
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "QuotedSpan".
 */
export interface QuotedSpan {
  passage_id: PassageId;
  text: Text1;
}
/**
 * What the model returns. Tagalog is written first (D02).
 *
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ReflectionDraft".
 */
export interface ReflectionDraft {
  en: En2;
  quoted_spans: QuotedSpans;
  tl: Tl2;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ReflectionOut".
 */
export interface ReflectionOut {
  layers: Layers;
  lesson_id: LessonId1;
  model: Model;
  prompt_version: PromptVersion;
  reflection: ReflectionDraft | null;
  status: Status;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ReviewAnswerIn".
 */
export interface ReviewAnswerIn {
  duration_ms: DurationMs1;
  exercise_id: ExerciseId2;
  response: Response1;
}
export interface Response1 {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ReviewAnswerOut".
 */
export interface ReviewAnswerOut {
  correct: Correct3;
  hearts: Hearts2;
  next_due_at: NextDueAt;
  session_answered: SessionAnswered;
  state: State;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ReviewDueOut".
 */
export interface ReviewDueOut {
  items: Items;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "ReviewItemOut".
 */
export interface ReviewItemOut {
  due_at: DueAt;
  exercise: ExerciseOut;
  reps: Reps;
  state: State1;
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
  id: Id3;
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
  id: Id4;
  order_index: OrderIndex1;
  slug: Slug1;
  status: Status1;
  title: Title1;
  xp_reward: XpReward;
}
/**
 * This interface was referenced by `RizalAIAPIContracts`'s JSON-Schema
 * via the `definition` "UserOut".
 */
export interface UserOut {
  hearts: Hearts3;
  id: Id5;
  last_activity_date: LastActivityDate;
  streak_count: StreakCount1;
  timezone: Timezone;
  total_xp: TotalXp1;
}
