import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { Icon } from '../components/Icon'
import type { Summary } from '../types'

function splitText(text: string) {
  const index = text.indexOf('：')
  if (index > 0) return { title: text.slice(0, index), body: text.slice(index + 1).trim() }
  return { title: '', body: text }
}

function formatDate(iso?: string | null, withTime = true) {
  if (!iso) return '时间未知'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '时间未知'
  const day = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }).format(date)
  if (!withTime) return day
  const time = new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }).format(date)
  return `${day} ${time}`
}

export function SummaryPage() {
  const { sessionId = '' } = useParams()
  const [summary, setSummary] = useState<Summary | null>(null)
  const [versions, setVersions] = useState<number>(0)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .listSummaries(sessionId)
      .then((list) => {
        setVersions(list.length)
        setSummary(list[list.length - 1] || null)
        if (!list.length) setError('这份探索还没有生成思考记录。')
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
  }, [sessionId])

  if (error) {
    return (
      <div className="container" style={{ padding: '72px 24px' }}>
        <p className="error-text">{error}</p>
        <Link to={`/dialogue/${sessionId}`} className="btn btn--ghost" style={{ marginTop: 16 }}>
          回到对话
        </Link>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="container" style={{ padding: '72px 24px' }}>
        <span className="spinner-line" /> <span style={{ marginLeft: 8, fontSize: 13 }}>正在整理思考记录…</span>
      </div>
    )
  }

  const recordNo = `TL-${summary.id.slice(-8).toUpperCase()}`

  return (
    <>
      <section className="record-hero">
        <div className="container" style={{ paddingTop: 20 }}>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 16,
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--line)',
              padding: '18px 0',
            }}
          >
            <div style={{ display: 'flex', gap: 10, fontSize: 10, letterSpacing: '0.12em', color: '#8c8476' }}>
              <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>
                THINKLAB
              </Link>
              <span>/</span>
              <span style={{ color: '#4b4a42' }}>我的思考</span>
              <span>/</span>
              <span style={{ color: '#4b4a42' }}>{summary.lens_name}</span>
            </div>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: '#8b8375' }}>一次完整的探索 / 04</div>
          </div>

          <div style={{ display: 'grid', gap: 40, padding: '48px 0', gridTemplateColumns: '1fr' }}>
            <div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
                <div className="eyebrow">THINKING RECORD</div>
                <span className="chip" style={{ borderColor: '#c8d2c1', background: '#eef1e8', color: '#52634e' }}>
                  <Icon name="check" size={10} /> 来自你的对话 · v{summary.version}
                </span>
              </div>
              <h1 className="font-display" style={{ marginTop: 20, maxWidth: 900, fontSize: 36, lineHeight: 1.48, letterSpacing: '-0.025em' }}>
                关于「<span style={{ color: '#9b4f35' }}>{summary.question.slice(0, 18)}</span>」
                <br />
                的思考记录
              </h1>
              <p className="font-display" style={{ marginTop: 24, maxWidth: 660, fontSize: 15, lineHeight: 1.95, color: '#6c6558' }}>
                这份记录不是结论，而是一张继续思考的地图。它保留了你走过的路径，也标出了仍未被回答的张力。
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, marginTop: 28, fontSize: 10, color: '#8e8779' }}>
                <span>
                  生成于 {formatDate(summary.created_at)} · {summary.lens_name} · {summary.turns} 轮追问
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <Icon name="bookmark" size={12} /> 已保存
                </span>
                {versions > 1 && <span>共 {versions} 个版本</span>}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container" style={{ padding: '48px 24px' }}>
        <div style={{ display: 'grid', gap: 48, gridTemplateColumns: '1fr' }}>
          <article>
            <section className="record-section" style={{ marginTop: 0, borderTop: 'none', paddingTop: 0 }}>
              <div>
                <span className="record-section__index">I</span>
                <div style={{ marginTop: 8, fontSize: 8, fontWeight: 600, letterSpacing: '0.18em', color: '#9a9182' }}>
                  THE QUESTION
                </div>
              </div>
              <div>
                <h2 className="font-display" style={{ margin: 0, fontSize: 27, color: '#282720' }}>
                  你带来的问题
                </h2>
                <div
                  style={{
                    marginTop: 20,
                    border: '1px solid #d4c8b5',
                    borderLeft: '2px solid #9b4f35',
                    background: 'var(--paper-soft)',
                    padding: 24,
                  }}
                >
                  <div style={{ display: 'flex', gap: 12 }}>
                    <span className="font-display" style={{ fontSize: 30, lineHeight: 1, color: '#b08a4b' }}>
                      “
                    </span>
                    <p className="font-display" style={{ margin: 0, fontSize: 19, lineHeight: 1.85, color: '#403c33' }}>
                      {summary.question}
                    </p>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', borderTop: '1px solid #ded3c1', marginTop: 20, paddingTop: 16 }}>
                    <span style={{ fontSize: 8, letterSpacing: '0.12em', color: '#9a9182' }}>本次选择的视角</span>
                    <span className="chip" style={{ borderColor: '#c8d2c1', background: '#eef1e8', color: '#52634e' }}>
                      {summary.lens_name}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 12, borderLeft: '1px solid var(--gold)', paddingLeft: 16, marginTop: 20 }}>
                  <Icon name="search" size={14} />
                  <p style={{ margin: 0, fontSize: 10, lineHeight: 1.85, color: '#7b7366' }}>
                    这条视角的核心追问：
                    <span className="font-display" style={{ fontSize: 11, color: '#555047' }}>
                      {summary.core_ask}
                    </span>
                  </p>
                </div>
              </div>
            </section>

            <section className="record-section">
              <div>
                <span className="record-section__index">II</span>
                <div style={{ marginTop: 8, fontSize: 8, fontWeight: 600, letterSpacing: '0.18em', color: '#9a9182' }}>
                  THE PATH
                </div>
              </div>
              <div>
                <h2 className="font-display" style={{ margin: 0, fontSize: 27, color: '#282720' }}>
                  这次探索的路径
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 16, marginTop: 28 }}>
                  {[
                    { n: '01', label: '提出问题', desc: '原始表述被如实保留' },
                    { n: '02', label: '选择目光', desc: summary.lens_name },
                    { n: '03', label: '展开对话', desc: `你留下了 ${summary.turns} 轮追问` },
                    { n: '04', label: '形成记录', desc: '记录已形成，仍可继续' },
                  ].map((item) => (
                    <div key={item.n} style={{ borderTop: '1px solid #cfc4b1', paddingTop: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="font-display" style={{ fontSize: 12, fontStyle: 'italic', color: '#b08a4b' }}>
                          {item.n}
                        </span>
                        <Icon name="check" size={11} />
                      </div>
                      <p style={{ margin: '8px 0 0', fontSize: 11, fontWeight: 500, color: '#4e4b42' }}>{item.label}</p>
                      <p style={{ margin: '4px 0 0', fontSize: 9, lineHeight: 1.75, color: '#91897b' }}>{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="record-section">
              <div>
                <span className="record-section__index">III</span>
                <div style={{ marginTop: 8, fontSize: 8, fontWeight: 600, letterSpacing: '0.18em', color: '#9a9182' }}>
                  INSIGHTS
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-end', gap: 12 }}>
                  <h2 className="font-display" style={{ margin: 0, fontSize: 27, color: '#282720' }}>
                    对话里浮现的洞见
                  </h2>
                  <span style={{ fontSize: 9, letterSpacing: '0.1em', color: '#9a9182' }}>
                    {String(summary.insights.length).padStart(2, '0')} POINTS
                  </span>
                </div>
                <div style={{ marginTop: 24 }}>
                  {summary.insights.map((insight, index) => {
                    const { title, body } = splitText(insight)
                    return (
                      <div className="insight-item" key={insight}>
                        <span className="font-display" style={{ fontSize: 13, fontStyle: 'italic', color: '#b08a4b' }}>
                          {String(index + 1).padStart(2, '0')}
                        </span>
                        <div>
                          {title && (
                            <h3 className="font-display" style={{ margin: 0, fontSize: 19, lineHeight: 1.55, color: '#343129' }}>
                              {title}
                            </h3>
                          )}
                          <p className="font-display" style={{ margin: title ? '8px 0 0' : 0, fontSize: 13.5, lineHeight: 1.95, color: '#71695c' }}>
                            {body}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </section>

            <section className="record-section">
              <div>
                <span className="record-section__index" style={{ color: '#9b4f35' }}>
                  IV
                </span>
                <div style={{ marginTop: 8, fontSize: 8, fontWeight: 600, letterSpacing: '0.18em', color: '#9a9182' }}>
                  TENSIONS
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-end', gap: 12 }}>
                  <h2 className="font-display" style={{ margin: 0, fontSize: 27, color: '#282720' }}>
                    尚未解开的张力
                  </h2>
                  <span style={{ fontSize: 9, letterSpacing: '0.1em', color: '#9a9182' }}>
                    {String(summary.tensions.length).padStart(2, '0')} TENSIONS
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginTop: 24 }}>
                  {summary.tensions.map((tension, index) => {
                    const { title, body } = splitText(tension)
                    return (
                      <div className="tension-card" key={tension}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2d1c5', paddingBottom: 12 }}>
                          <span style={{ fontSize: 8, fontWeight: 600, letterSpacing: '0.14em', color: '#9b4f35' }}>
                            TENSION {String(index + 1).padStart(2, '0')}
                          </span>
                          <Icon name="fork" size={14} />
                        </div>
                        <h3 className="font-display" style={{ margin: '16px 0 0', fontSize: 16, lineHeight: 1.6, color: '#573c31' }}>
                          {title || '一处尚未解开的矛盾'}
                        </h3>
                        <p style={{ margin: '8px 0 0', fontSize: 11, lineHeight: 1.9, color: '#7c5f53' }}>{body}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            </section>

            <section className="record-section">
              <div>
                <span className="record-section__index" style={{ color: '#52634e' }}>
                  V
                </span>
                <div style={{ marginTop: 8, fontSize: 8, fontWeight: 600, letterSpacing: '0.18em', color: '#9a9182' }}>
                  PRACTICE
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-end', gap: 12 }}>
                  <h2 className="font-display" style={{ margin: 0, fontSize: 27, color: '#282720' }}>
                    可以带走的实践
                  </h2>
                  <span style={{ fontSize: 9, letterSpacing: '0.1em', color: '#9a9182' }}>
                    {String(summary.practices.length).padStart(2, '0')} ACTIONS
                  </span>
                </div>
                <div style={{ marginTop: 20, borderTop: '1px solid var(--line)' }}>
                  {summary.practices.map((practice, index) => (
                    <label className="practice-row" key={practice}>
                      <input type="checkbox" style={{ marginTop: 4, accentColor: '#52634e' }} />
                      <span className="font-display" style={{ fontSize: 10, fontStyle: 'italic', color: '#b08a4b' }}>
                        {String(index + 1).padStart(2, '0')}
                      </span>
                      <span>{practice}</span>
                    </label>
                  ))}
                  <p style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, fontSize: 9, color: '#9a9182' }}>
                    <Icon name="list" size={11} /> 不必全部完成。选一个最轻的，先开始。
                  </p>
                </div>
              </div>
            </section>

            <section className="record-section">
              <div>
                <span className="record-section__index">VI</span>
                <div style={{ marginTop: 8, fontSize: 8, fontWeight: 600, letterSpacing: '0.18em', color: '#9a9182' }}>
                  EXCERPTS
                </div>
              </div>
              <div>
                <h2 className="font-display" style={{ margin: 0, fontSize: 27, color: '#282720' }}>
                  对话里的原话
                </h2>
                <div style={{ marginTop: 24, borderTop: '1px solid var(--line)' }}>
                  {summary.excerpts.length === 0 && (
                    <p style={{ padding: '24px 0', fontSize: 11, color: '#91897b' }}>这次探索还没有留下可摘录的原话。</p>
                  )}
                  {summary.excerpts.map((excerpt, index) => (
                    <div className="excerpt-item" key={`${excerpt.role}-${index}`}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 8 }}>
                        <span
                          className="chip"
                          style={{
                            borderColor: excerpt.role === 'user' ? '#d2b7a8' : '#c8d2c1',
                            background: excerpt.role === 'user' ? '#f5e8e0' : '#edf1e8',
                            color: excerpt.role === 'user' ? '#8a4b35' : '#52634e',
                          }}
                        >
                          {excerpt.role === 'user' ? '你' : '哲学 Agent'}
                        </span>
                      </div>
                      <p
                        className="font-display"
                        style={{
                          margin: '12px 0 0',
                          borderLeft: '1px solid #d3c6b2',
                          paddingLeft: 16,
                          fontSize: 13,
                          lineHeight: 1.95,
                          color: '#5e594f',
                        }}
                      >
                        “{excerpt.text}”
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #cfc4b1', marginTop: 48, paddingTop: 28 }}>
              <div style={{ display: 'flex', gap: 12, maxWidth: 540 }}>
                <Icon name="compass" size={18} />
                <p className="font-display" style={{ margin: 0, fontSize: 12, lineHeight: 1.85, color: '#7b7366' }}>
                  这张记录不是终点。你随时可以带着新的困惑回到原处，或换一副眼镜重新看同一个问题。
                </p>
              </div>
              <Link to={`/dialogue/${sessionId}`} className="btn">
                继续这段对话
                <Icon name="arrow-up-right" size={14} />
              </Link>
            </div>
          </article>
        </div>

        <p style={{ marginTop: 32, fontSize: 9, color: '#9a9182' }}>记录编号：{recordNo}</p>
      </div>
    </>
  )
}
