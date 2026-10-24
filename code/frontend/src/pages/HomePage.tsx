import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Icon } from '../components/Icon'

const SAMPLES = [
  '我总在担心自己做得不够好，如何面对这种持续的焦虑？',
  '我有一份稳定的工作，却总觉得这不是我想要的人生。我该不该改变？',
]

const STEPS = [
  {
    index: '01',
    title: '说出一个真实的问题',
    desc: '不是宏大的哲学命题，而是你此刻真正卡住的地方：一段关系、一次选择、一种反复出现的情绪。',
    icon: 'pen' as const,
  },
  {
    index: '02',
    title: '看见三种哲学目光',
    desc: '斯多葛主义、存在主义、道家，各自从不同方向照亮同一个处境。它们不是标准答案，而是三副可以试戴的眼镜。',
    icon: 'glasses' as const,
  },
  {
    index: '03',
    title: '选择一条路径，深入对话',
    desc: '你决定从哪里进入。Agent 会守住这个视角，也会追问那些被快速结论遮住的部分，陪你多轮往下走。',
    icon: 'messages' as const,
  },
  {
    index: '04',
    title: '留下记录，然后继续',
    desc: '随时生成一份结构化的思考记录：洞见、张力与下一步实践。但它不是终点，你可以带着新的问题回到对话。',
    icon: 'bookmark' as const,
  },
]

export function HomePage() {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    const value = question.trim()
    if (!value) {
      setError('请先写下一个你真正关心的问题。')
      return
    }
    setLoading(true)
    setError('')
    try {
      const session = await api.createSession(value)
      navigate(`/perspectives/${session.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建探索失败')
      setLoading(false)
    }
  }

  return (
    <>
      <section className="hero">
        <div className="container hero__grid">
          <div>
            <div className="eyebrow">PHILOSOPHICAL AI AGENT</div>
            <h1 className="hero__title">
              把现实的困惑，
              <br />
              交给哲学
              <br />
              <span style={{ color: '#9b4f35' }}>重新照亮。</span>
            </h1>
            <p className="hero__lead">
              ThinkLab 不急着给你答案。它会从三种彼此不同的哲学传统出发，陪你重新看见问题，选择一条真正想走下去的路径。
            </p>
            <div className="hero__meta">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Icon name="glasses" size={14} /> 三种视角
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Icon name="messages" size={14} /> 多轮追问
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Icon name="bookmark" size={14} /> 思考记录
              </span>
            </div>
            <figure className="quote-block" style={{ marginTop: 40, maxWidth: 460 }}>
              <blockquote className="font-display" style={{ margin: 0, fontSize: 14, lineHeight: 1.85, color: '#756e60' }}>
                “未经审视的人生不值得过。”
              </blockquote>
              <figcaption style={{ marginTop: 8, fontSize: 10, letterSpacing: '0.16em', color: '#9a9283' }}>
                苏格拉底 · 申辩篇
              </figcaption>
            </figure>
          </div>

          <div id="composer">
            <div className="composer">
              <div className="composer__inner">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 10, fontWeight: 600, letterSpacing: '0.19em', color: '#52634e' }}>
                    <span style={{ width: 6, height: 6, borderRadius: 999, background: '#9b4f35' }} />
                    CURRENT INQUIRY
                  </span>
                  <span className="font-display" style={{ fontSize: 12, fontStyle: 'italic', color: '#9a9283' }}>
                    01 / 提问
                  </span>
                </div>

                <h2 className="composer__title">
                  此刻，有什么事
                  <br />
                  正在你心里反复出现？
                </h2>
                <p style={{ marginTop: 8, fontSize: 11, lineHeight: 1.8, color: '#8a8375' }}>
                  一个具体的现实处境，比一个抽象的大问题更适合开始。
                </p>

                <div className="field" style={{ marginTop: 20 }}>
                  <textarea
                    className="field-input"
                    rows={5}
                    maxLength={300}
                    value={question}
                    placeholder="例如：我总在担心自己做得不够好，如何面对这种持续的焦虑？"
                    onChange={(event) => {
                      setQuestion(event.target.value)
                      if (error) setError('')
                    }}
                  />
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      borderTop: '1px solid #ded4c2',
                      padding: '8px 16px',
                      fontSize: 10,
                      color: '#9a9283',
                    }}
                  >
                    <span>不必完整，也不必正确。</span>
                    <span>{question.length} / 300</span>
                  </div>
                </div>

                {error && <p className="error-text" style={{ marginTop: 8 }}>{error}</p>}

                <div style={{ marginTop: 16 }}>
                  <p style={{ marginBottom: 8, fontSize: 10, letterSpacing: '0.12em', color: '#8f887a' }}>
                    或者，从一个相似的处境开始
                  </p>
                  <div className="sample-list">
                    {SAMPLES.map((sample) => (
                      <button key={sample} type="button" className="sample-chip" onClick={() => setQuestion(sample)}>
                        {sample.slice(0, 12)}…
                      </button>
                    ))}
                  </div>
                </div>

                <button type="button" className="btn btn--block" style={{ marginTop: 24 }} disabled={loading} onClick={submit}>
                  <span>{loading ? '正在生成三种目光…' : '让三种目光出现'}</span>
                  {loading ? <span className="spinner-line" /> : <Icon name="arrow-up-right" size={17} />}
                </button>

                <div style={{ display: 'flex', gap: 8, marginTop: 16, fontSize: 10, lineHeight: 1.7, color: '#918a7c' }}>
                  <Icon name="lock" size={13} />
                  <span>Agent 不会替你做决定。你保留选择、怀疑与改变主意的自由。</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="quote-band">
        <div className="container quote-band__inner">
          <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            <span className="font-display" style={{ fontSize: 52, lineHeight: 1, color: '#b08a4b' }}>
              “
            </span>
            <p className="font-display" style={{ margin: 0, maxWidth: 860, fontSize: 21, lineHeight: 1.8, color: '#f4eddf' }}>
              哲学并不替你决定怎样生活，它只是让你看清：自己正站在哪里，以及还可以往哪里看。
            </p>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              borderTop: '1px solid #5a6a5b',
              paddingTop: 20,
            }}
          >
            <span
              className="font-display"
              style={{
                display: 'grid',
                placeItems: 'center',
                width: 48,
                height: 48,
                borderRadius: 999,
                border: '1px solid #7f8f7c',
                color: '#d8c8a8',
                fontSize: 13,
              }}
            >
              思
            </span>
            <div>
              <div style={{ fontSize: 10, letterSpacing: '0.18em', color: '#aab8a5' }}>THINKLAB PRINCIPLE</div>
              <div className="font-display" style={{ marginTop: 4, fontSize: 13, fontStyle: 'italic', color: '#e7dfcd' }}>
                A method, not an answer.
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="method" style={{ borderBottom: '1px solid var(--line)' }}>
        <div className="container" style={{ padding: '72px 24px' }}>
          <div style={{ display: 'grid', gap: 48, gridTemplateColumns: '1fr' }}>
            <div>
              <div className="eyebrow">HOW IT WORKS</div>
              <h2 className="section-title" style={{ marginTop: 20 }}>
                一次完整的思考，
                <br />
                如何发生？
              </h2>
              <p className="font-display" style={{ marginTop: 24, maxWidth: 380, fontSize: 15, lineHeight: 1.95, color: '#70695c' }}>
                思考不是抵达某个漂亮结论，而是在不同的解释之间走动，直到你更清楚自己为何这样选择。
              </p>
            </div>
            <div className="steps">
              {STEPS.map((step) => (
                <div className="step-row" key={step.index}>
                  <span className="step-row__index">{step.index}</span>
                  <div>
                    <h3 className="step-row__title">{step.title}</h3>
                    <p className="step-row__desc">{step.desc}</p>
                  </div>
                  <Icon name={step.icon} size={22} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
