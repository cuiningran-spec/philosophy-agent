import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, streamMessage } from '../api'
import { Composer } from '../components/Composer'
import { Icon } from '../components/Icon'
import { MessageBubble, TypingIndicator } from '../components/MessageBubble'
import { Steps } from '../components/Steps'
import type { Lens, Message, SessionDetail, Summary } from '../types'

export function DialoguePage() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()
  const scrollRef = useRef<HTMLDivElement>(null)

  const [session, setSession] = useState<SessionDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState('')
  const [busy, setBusy] = useState(false)
  const [summarizing, setSummarizing] = useState(false)
  const [error, setError] = useState('')
  const [latestSummary, setLatestSummary] = useState<Summary | null>(null)

  const load = async () => {
    const data = await api.getSession(sessionId)
    setSession(data)
    setMessages(data.messages)
    if (data.summary_count > 0) {
      const list = await api.listSummaries(sessionId)
      setLatestSummary(list[list.length - 1] || null)
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, streaming])

  const lens: Lens | null = useMemo(() => {
    if (!session?.lens) return null
    return session.perspectives.find((item) => item.key === session.lens) || null
  }, [session])

  useEffect(() => {
    if (session && !session.lens) {
      navigate(`/perspectives/${sessionId}`, { replace: true })
    }
  }, [session, sessionId, navigate])

  const turnCount = messages.filter((m) => m.role === 'user').length
  const lastUser = [...messages].reverse().find((m) => m.role === 'user')
  const stale = Boolean(
    latestSummary && lastUser?.created_at && new Date(lastUser.created_at) > new Date(latestSummary.created_at || 0),
  )

  const send = async (text: string) => {
    if (!session || busy) return
    setBusy(true)
    setError('')
    setStreaming('')
    const optimistic: Message = {
      id: `pending-${Date.now()}`,
      role: 'user',
      content: text,
      turn_index: turnCount + 1,
      seq: 9999,
      created_at: new Date().toISOString(),
      sources: [],
    }
    setMessages((prev) => [...prev, optimistic])

    try {
      await streamMessage(sessionId, text, {
        onUser: (message) =>
          setMessages((prev) => [...prev.filter((m) => m.id !== optimistic.id), message]),
        onToken: (chunk) => setStreaming((prev) => prev + chunk),
        onDone: ({ message }) => {
          setStreaming('')
          setMessages((prev) => [...prev.filter((m) => m.id !== optimistic.id), message])
          api.getSession(sessionId).then(setSession).catch(() => undefined)
        },
        onError: async (message) => {
          // SSE 不可用时退化为一次性接口
          try {
            const result = await api.sendMessage(sessionId, text)
            setMessages((prev) => [
              ...prev.filter((m) => m.id !== optimistic.id),
              result.user_message,
              result.agent_message,
            ])
          } catch {
            setError(message || '发送失败')
          }
          setStreaming('')
        },
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送失败')
    } finally {
      setBusy(false)
    }
  }

  const generateSummary = async () => {
    if (!session || summarizing) return
    setSummarizing(true)
    setError('')
    try {
      await api.createSummary(sessionId)
      navigate(`/summary/${sessionId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '总结生成失败')
      setSummarizing(false)
    }
  }

  if (!session) {
    return (
      <div className="container" style={{ padding: '72px 24px' }}>
        <span className="spinner-line" /> <span style={{ marginLeft: 8, fontSize: 13 }}>正在进入这次探索…</span>
      </div>
    )
  }

  const accent = lens?.accent || '#43563f'

  return (
    <div className="dialogue-layout">
      <aside className="sidebar">
        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #d5cab7', paddingBottom: 14 }}>
          <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: '0.18em', color: '#8c8476' }}>
            EXPLORATION / 02
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 8, letterSpacing: '0.1em', color: '#52634e' }}>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: '#52634e' }} />
            LIVE
          </span>
        </div>

        <h2 className="font-display" style={{ marginTop: 24, fontSize: 23 }}>
          本次探索
        </h2>
        <p style={{ marginTop: 4, fontSize: 10, letterSpacing: '0.1em', color: '#928a7c' }}>
          ONE QUESTION, ONE PATH
        </p>

        <div style={{ marginTop: 20, borderLeft: '2px solid var(--gold)', paddingLeft: 14 }}>
          <p style={{ margin: 0, fontSize: 8, letterSpacing: '0.14em', color: '#9a9182' }}>YOUR QUESTION</p>
          <p className="font-display" style={{ marginTop: 8, fontSize: 13, lineHeight: 1.85, color: '#514c41' }}>
            {session.question}
          </p>
        </div>

        <div style={{ marginTop: 32, borderTop: '1px solid #d5cab7', paddingTop: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <p style={{ margin: 0, fontSize: 8, fontWeight: 600, letterSpacing: '0.17em', color: '#91897b' }}>
              THE PATH
            </p>
            <p style={{ margin: 0, fontSize: 8, color: '#a29989' }}>03 / 04</p>
          </div>
          <Steps
            current={3}
            viewName={session.lens_name}
            turns={turnCount}
            hasSummary={Boolean(latestSummary)}
            stale={stale}
          />
        </div>

        {lens && (
          <div
            style={{
              marginTop: 28,
              border: '1px solid var(--line)',
              borderLeft: `3px solid ${lens.accent}`,
              background: 'var(--paper-light)',
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span
                style={{
                  display: 'grid',
                  placeItems: 'center',
                  width: 36,
                  height: 36,
                  borderRadius: 999,
                  border: `1px solid ${lens.line}`,
                  background: lens.soft,
                  color: lens.accent,
                }}
              >
                <Icon name={lens.key === 'stoic' ? 'columns' : lens.key === 'taoist' ? 'waves' : 'compass'} size={17} />
              </span>
              <div style={{ minWidth: 0 }}>
                <div className="font-display" style={{ fontSize: 15, lineHeight: 1.2 }}>
                  {lens.name}
                </div>
                <div style={{ marginTop: 4, fontSize: 8, letterSpacing: '0.14em', color: '#8b8375' }}>{lens.en}</div>
              </div>
            </div>
            <p style={{ margin: '14px 0 0', fontSize: 8, letterSpacing: '0.12em', color: '#948b7d' }}>
              当前视角的核心追问
            </p>
            <p className="font-display" style={{ margin: '6px 0 0', fontSize: 12, lineHeight: 1.75, color: '#555047' }}>
              {lens.core_ask}
            </p>
          </div>
        )}

        <Link
          to={`/perspectives/${sessionId}`}
          style={{
            marginTop: 16,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            border: '1px solid #cbbfab',
            padding: '10px 14px',
            fontSize: 10,
            color: '#71695c',
            textDecoration: 'none',
          }}
        >
          换一个视角
          <Icon name="replace" size={13} />
        </Link>

        <div style={{ marginTop: 'auto', paddingTop: 28 }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 9, color: '#938b7d', textDecoration: 'none' }}>
            <Icon name="arrow-left" size={12} /> 离开这次探索
          </Link>
        </div>
      </aside>

      <section className="chat">
        <div style={{ flexShrink: 0, borderBottom: '1px solid #e1d7c6', background: '#fbf8f1', padding: '16px 24px' }}>
          <div style={{ width: '100%', maxWidth: 840, margin: '0 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 9, fontWeight: 600, letterSpacing: '0.2em', color: '#8b8375' }}>
                <span style={{ width: 4, height: 4, borderRadius: 999, background: '#9b4f35' }} />
                LIVE DIALOGUE
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {latestSummary && (
                  <span
                    className="chip"
                    style={{
                      borderColor: stale ? '#dcc8a8' : '#c8d2c1',
                      background: stale ? '#f5ecdc' : '#eef1e8',
                      color: stale ? '#8a6234' : '#52634e',
                    }}
                  >
                    <Icon name={stale ? 'refresh' : 'check'} size={10} />
                    {stale ? '记录可更新' : '已生成记录'}
                  </span>
                )}
                <button
                  type="button"
                  onClick={generateSummary}
                  disabled={summarizing}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    border: 'none',
                    background: 'transparent',
                    color: '#8a4b35',
                    fontSize: 10,
                    textDecoration: 'underline',
                    cursor: 'pointer',
                  }}
                >
                  随时留下记录
                  <Icon name="arrow-right" size={11} />
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12, marginTop: 10 }}>
              <div>
                <h1 className="font-display" style={{ margin: 0, fontSize: 25, lineHeight: 1.35, letterSpacing: '-0.015em' }}>
                  与 <span style={{ color: accent }}>{session.lens_name || '哲学'}</span> 的对话
                </h1>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8, marginTop: 8 }}>
                  <span
                    className="chip"
                    style={{ borderColor: lens?.line, background: lens?.soft, color: accent }}
                  >
                    <span style={{ width: 6, height: 6, borderRadius: 999, background: accent }} />
                    当前视角 · {session.lens_name}
                  </span>
                  <span style={{ fontSize: 10, color: '#958d7f' }}>
                    {turnCount === 0 ? '尚未开始追问' : `第 ${turnCount} 轮追问`}
                  </span>
                  <span style={{ fontSize: 10, color: '#a09787' }}>· 总结后仍可继续</span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p className="font-display" style={{ margin: 0, fontSize: 11, fontStyle: 'italic', color: '#8c8476' }}>
                  {lens?.tagline}
                </p>
                <p style={{ margin: '4px 0 0', fontSize: 8, letterSpacing: '0.1em', color: '#a29989' }}>
                  VIEW LOCKED · THOUGHT OPEN
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="chat__scroll" ref={scrollRef}>
          <div className="chat__list">
            {latestSummary && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  border: '1px solid #d5c7b1',
                  background: '#f5efe3',
                  padding: '12px 16px',
                  marginBottom: 26,
                }}
              >
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <Icon name={stale ? 'refresh' : 'bookmark'} size={14} />
                  <p style={{ margin: 0, fontSize: 10, lineHeight: 1.8, color: '#7b7366' }}>
                    {stale
                      ? '思考记录生成之后，你又继续了对话。你可以回到记录页查看旧版，或稍后重新生成一份更新版。'
                      : '一份思考记录已经形成。对话没有被结束，你可以从这里继续追问，旧的记录会保留下来。'}
                  </p>
                </div>
                <Link to={`/summary/${sessionId}`} style={{ fontSize: 10, color: '#8a4b35' }}>
                  查看记录 →
                </Link>
              </div>
            )}

            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} lens={lens} />
            ))}

            {streaming && (
              <MessageBubble
                message={{
                  id: 'streaming',
                  role: 'agent',
                  content: streaming,
                  turn_index: turnCount,
                  seq: 99999,
                  created_at: new Date().toISOString(),
                  sources: [],
                }}
                lens={lens}
                streaming
              />
            )}

            {busy && !streaming && <TypingIndicator accent={accent} />}
          </div>
        </div>

        {error && (
          <div style={{ padding: '0 24px 8px' }}>
            <p className="error-text">{error}</p>
          </div>
        )}

        <div className="composer-bar">
          <Composer
            chips={lens?.prompts || []}
            busy={busy}
            placeholder={lens ? `从「${lens.core_ask}」说起，或写下此刻想到的第一句话…` : undefined}
            onSubmit={send}
          />
          <p style={{ margin: '6px 0 0', textAlign: 'center', fontSize: 10, color: '#a69d8e' }}>
            ThinkLab 提供思考路径，不替你做决定。
          </p>
        </div>
      </section>

      <aside className="sidebar sidebar--right">
        <div style={{ position: 'relative', overflow: 'hidden', background: '#2f4034', color: '#f8f2e5', padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #5a6a5a', paddingBottom: 12 }}>
            <span style={{ fontSize: 8, fontWeight: 600, letterSpacing: '0.19em', color: '#bcc7b6' }}>SYNTHESIS</span>
            <Icon name="scroll" size={16} />
          </div>
          <h2 className="font-display" style={{ marginTop: 16, fontSize: 21, lineHeight: 1.5, color: '#fbf6e9' }}>
            把此刻的思考，
            <br />
            留下来。
          </h2>
          <p style={{ marginTop: 10, fontSize: 10, lineHeight: 1.9, color: '#b7c1b1' }}>
            基于当前对话，整理成一份包含洞见、张力与下一步实践的思考记录。
          </p>
          <button
            type="button"
            className="btn btn--block"
            style={{ marginTop: 20, background: '#d4b98c', borderColor: '#d4b98c', color: '#283529' }}
            onClick={generateSummary}
            disabled={summarizing}
          >
            {summarizing ? '正在整理…' : '生成思考总结'}
            <Icon name="arrow-up-right" size={15} />
          </button>
          {latestSummary && (
            <Link
              to={`/summary/${sessionId}`}
              style={{ display: 'inline-flex', marginTop: 12, gap: 6, fontSize: 9, color: '#d9c6a4' }}
            >
              查看{stale ? '上次记录' : '思考记录'}
              <Icon name="arrow-right" size={11} />
            </Link>
          )}
          <p style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 12, fontSize: 8, color: '#9eaa98' }}>
            <Icon name="refresh" size={10} /> 生成后仍可继续对话
          </p>
        </div>

        <div style={{ marginTop: 24, borderTop: '1px solid #d2c6b2', paddingTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ margin: 0, fontSize: 8, fontWeight: 600, letterSpacing: '0.17em', color: '#8c8476' }}>
              THREAD NOTES
            </p>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 8, color: '#9a9283' }}>
              <span style={{ width: 4, height: 4, borderRadius: 999, background: '#b08a4b' }} /> 实时
            </span>
          </div>
          <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
            <div>
              <p style={{ margin: 0, fontSize: 8, letterSpacing: '0.1em', color: '#a19889' }}>你正在处理</p>
              <p className="font-display" style={{ margin: '4px 0 0', fontSize: 11, lineHeight: 1.75, color: '#5e594f' }}>
                {session.question}
              </p>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: 8, letterSpacing: '0.1em', color: '#a19889' }}>当前视角关注</p>
              <p className="font-display" style={{ margin: '4px 0 0', fontSize: 11, lineHeight: 1.75, color: '#5e594f' }}>
                {session.core_ask}
              </p>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: 8, letterSpacing: '0.1em', color: '#a19889' }}>你最近提到</p>
              <p style={{ margin: '4px 0 0', borderLeft: '1px solid #c8bba5', paddingLeft: 10, fontSize: 10, lineHeight: 1.8, color: '#746c5f' }}>
                {lastUser?.content || '还没有开始追问。从下面的建议里选一个方向，或写下此刻想到的第一句话。'}
              </p>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 24, borderTop: '1px solid #d2c6b2', paddingTop: 16 }}>
          <p style={{ margin: 0, fontSize: 8, fontWeight: 600, letterSpacing: '0.17em', color: '#8c8476' }}>
            A RECORD WILL HOLD
          </p>
          <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>
            {[
              { n: '03', text: '三个逐渐清晰的洞见' },
              { n: '02', text: '两处尚未解开的张力' },
              { n: '03', text: '三个可以带走的实践' },
            ].map((item) => (
              <div key={item.n} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 9, color: '#7b7366' }}>
                <span
                  className="font-display"
                  style={{
                    display: 'grid',
                    placeItems: 'center',
                    width: 24,
                    height: 24,
                    border: '1px solid #d3c6b3',
                    background: 'var(--paper-light)',
                    color: '#9b4f35',
                    fontSize: 9,
                  }}
                >
                  {item.n}
                </span>
                {item.text}
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 'auto', display: 'flex', gap: 6, borderTop: '1px solid #d2c6b2', paddingTop: 16, fontSize: 8, color: '#9c9384' }}>
          <Icon name="lock" size={11} /> 对话与记录保存在服务端数据库中
        </div>
      </aside>
    </div>
  )
}
