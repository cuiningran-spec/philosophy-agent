import type {
  FaqAnswer,
  FaqEntry,
  HealthInfo,
  Lens,
  LensKey,
  Message,
  SessionBrief,
  SessionDetail,
  Summary,
} from './types'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) || '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const data = await response.json()
      detail = data?.detail || detail
    } catch {
      /* 忽略解析失败 */
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

export const api = {
  health: () => request<HealthInfo>('/health'),

  createSession: (question: string) =>
    request<SessionDetail>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  getSession: (id: string) => request<SessionDetail>(`/sessions/${id}`),

  listSessions: (limit = 20) => request<SessionBrief[]>(`/sessions?limit=${limit}`),

  selectLens: (id: string, lens: LensKey, keepHistory = true) =>
    request<SessionDetail>(`/sessions/${id}/lens`, {
      method: 'POST',
      body: JSON.stringify({ lens, keep_history: keepHistory }),
    }),

  sendMessage: (id: string, content: string) =>
    request<{ user_message: Message; agent_message: Message }>(
      `/sessions/${id}/messages`,
      { method: 'POST', body: JSON.stringify({ content }) },
    ),

  listLenses: () => request<Lens[]>('/lenses'),

  createSummary: (id: string) =>
    request<Summary>(`/sessions/${id}/summaries`, { method: 'POST' }),

  listSummaries: (id: string) => request<Summary[]>(`/sessions/${id}/summaries`),

  getSummary: (summaryId: string) => request<Summary>(`/summaries/${summaryId}`),

  askFaq: (question: string) =>
    request<FaqAnswer>('/faq/ask', { method: 'POST', body: JSON.stringify({ question }) }),

  listFaq: () => request<FaqEntry[]>('/faq'),
}

export interface StreamHandlers {
  onUser?: (message: Message) => void
  onToken?: (text: string) => void
  onDone?: (payload: { message: Message }) => void
  onError?: (message: string) => void
}

/** SSE 流式发送消息：user → token* → done */
export async function streamMessage(
  sessionId: string,
  content: string,
  handlers: StreamHandlers,
): Promise<void> {
  const response = await fetch(`${BASE}/sessions/${sessionId}/messages/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
  if (!response.ok || !response.body) {
    handlers.onError?.(`发送失败：${response.status}`)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      const lines = block.split('\n')
      let event = 'message'
      const dataLines: string[] = []
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
      }
      if (!dataLines.length) continue
      const payload = JSON.parse(dataLines.join('\n'))
      if (event === 'token') handlers.onToken?.(payload.content)
      else if (event === 'user') handlers.onUser?.(payload.message)
      else if (event === 'done') handlers.onDone?.(payload)
      else if (event === 'error') handlers.onError?.(payload.message)
    }
  }
}
