import { useEffect, useState } from 'react'
import { api } from '../api'
import { Icon } from '../components/Icon'
import type { FaqAnswer, FaqEntry } from '../types'

export function FaqPage() {
  const [entries, setEntries] = useState<FaqEntry[]>([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<FaqAnswer | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listFaq().then(setEntries).catch(() => setEntries([]))
  }, [])

  const ask = async (value: string) => {
    const text = value.trim()
    if (!text || loading) return
    setLoading(true)
    setError('')
    try {
      setAnswer(await api.askFaq(text))
    } catch (err) {
      setError(err instanceof Error ? err.message : '问答失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container" style={{ padding: '56px 24px' }}>
      <div className="eyebrow">FAQ / KNOWLEDGE BASE</div>
      <h1 className="section-title" style={{ marginTop: 20 }}>
        向知识库提问
      </h1>
      <p className="font-display" style={{ marginTop: 20, maxWidth: 620, fontSize: 15, lineHeight: 1.95, color: '#6c6558' }}>
        Agent 会先在哲学知识库里检索相关语料，再组织答案；命中的条目会一并显示在答案下方，便于你追溯出处。
      </p>

      <div className="field" style={{ marginTop: 32, maxWidth: 760 }}>
        <textarea
          className="field-input"
          rows={3}
          value={question}
          placeholder="例如：道家的“无为”是不是躺平？"
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              ask(question)
            }
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #e3dacb', padding: '8px 16px' }}>
          <span style={{ fontSize: 10, color: '#a09787' }}>Enter 发送 · Shift + Enter 换行</span>
          <button type="button" className="btn" disabled={loading} onClick={() => ask(question)}>
            {loading ? '检索中…' : '提问'}
            <Icon name="search" size={13} />
          </button>
        </div>
      </div>

      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}

      {answer && (
        <div className="card" style={{ marginTop: 28, maxWidth: 760, padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, borderBottom: '1px solid var(--line)', paddingBottom: 12 }}>
            <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: '0.18em', color: '#8a4b35' }}>
              ANSWER
            </span>
            {answer.matched && (
              <span style={{ fontSize: 10, color: '#8a8375' }}>命中条目：{answer.matched}</span>
            )}
          </div>
          <p className="font-display" style={{ margin: '18px 0 0', fontSize: 15, lineHeight: 1.95, color: '#403c33' }}>
            {answer.answer}
          </p>
          {answer.sources.length > 0 && (
            <div style={{ marginTop: 20, borderTop: '1px dashed #ded3c1', paddingTop: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: '#8a8274' }}>
                <Icon name="search" size={12} /> 检索来源
              </div>
              <ul style={{ margin: '10px 0 0', paddingLeft: 18, fontSize: 11, lineHeight: 1.9, color: '#6b6559' }}>
                {answer.sources.map((source) => (
                  <li key={source.doc_id || source.title}>
                    {source.title}
                    {source.thinker ? ` · ${source.thinker}` : ''}
                    <span style={{ color: '#a09787' }}> （{source.school}）</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <h2 className="font-display" style={{ marginTop: 56, fontSize: 24, color: '#2d2c26' }}>
        常见问题
      </h2>
      <div style={{ maxWidth: 760, marginTop: 8 }}>
        {entries.map((entry) => (
          <div className="faq-item" key={entry.faq_id}>
            <h3 className="faq-question">{entry.question}</h3>
            <p className="faq-answer">{entry.answer}</p>
            <button
              type="button"
              className="btn btn--ghost"
              style={{ marginTop: 12, padding: '6px 12px', fontSize: 10 }}
              onClick={() => {
                setQuestion(entry.question)
                ask(entry.question)
              }}
            >
              向 Agent 追问这个条目
              <Icon name="arrow-right" size={12} />
            </button>
          </div>
        ))}
        {entries.length === 0 && <p className="empty-state">知识库暂无 FAQ 条目。</p>}
      </div>
    </div>
  )
}
