// utils.ts
export function validateQuestionInput(question: string): boolean {
  return question.trim().length > 0;
}