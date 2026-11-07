// utils.test.ts
import { describe, it, expect } from 'vitest';
import { validateQuestionInput } from './utils';

describe('前端输入校验测试', () => {
  it('输入空字符串应返回 false', () => {
    expect(validateQuestionInput("")).toBe(false);
    expect(validateQuestionInput("   ")).toBe(false);
  });

  it('输入有效问题应返回 true', () => {
    expect(validateQuestionInput("探讨一下哲学")).toBe(true);
  });
});