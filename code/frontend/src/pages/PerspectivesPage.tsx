import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { Icon } from '../components/Icon'
import { LensCard } from '../components/LensCard'
import type { Lens, SessionDetail } from '../types'

const COMPARE: { dimension: string; items: string[] }[] = [
  {
    dimension: '问题从哪里来',
    items: [
      '往往来自我们对事实追加的判断',
      '来自必须由自己承担的自由与不确定性',
      '来自人为的执念，以及与事物本性的对抗',
    ],
  },
  {
    dimension: '自由在哪里',
    items: [
      '在判断、选择与当下能完成的行动里',
      '在承认没有标准答案后，仍为自己的选择负责',
      '在顺势而为、不过度用力的分寸里',
    ],
  },
  {
    dimension: '第一步会问你',
    items: ['“哪一部分真正由你决定？”', '“如果无人评价，你会怎么选？”', '“你正在与什么较劲？”'],
  },
  {
    dimension: '它不承诺',
    items: [
      '消除痛苦，只训练更清醒的回应',
      '提供正确答案，只让你更诚实地选择',
      '让你退出世界，只让你少一点强行',
    ],
  },
]

export function PerspectivesPage() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [error, setError] = useState('')
  const [selecting, setSelecting] = useState<string | null>(null)

  useEffect(() => {
    api
      .getSession(sessionId)
      .then(setSession)
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
  }, [sessionId])

  const choose = useCallback(
    async (lens: Lens) => {
      setSelecting(lens.key)
      try {
        await api.selectLens(sessionId, lens.key)
        navigate(`/dialogue/${sessionId}`)
      } catch (err) {
        setError(err instanceof Error ? err.message : '选择视角失败')
        setSelecting(null)
      }
    },
    [navigate, sessionId],
  )

  if (error) {
    return (
      <div className="container" style={{ padding: '72px 24px' }}>
        <p className="error-text">{error}</p>
        <Link to="/" className="btn btn--ghost" style={{ marginTop: 16 }}>
          重新提出问题
        </Link>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="container" style={{ padding: '72px 24px' }}>
        <span className="spinner-line" /> <span style={{ marginLeft: 8, fontSize: 13 }}>正在生成三种目光…</span>
      </div>
    )
  }

  return (
    <>
      <section style={{ borderBottom: '1px solid var(--line)' }}>
        <div className="container" style={{ paddingTop: 32, paddingBottom: 40 }}>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 16,
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--line)',
              paddingBottom: 20,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 10, letterSpacing: '0.12em', color: '#8c8476' }}>
              <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>
                THINKLAB
              </Link>
              <span>/</span>
              <span style={{ color: '#4b4a42' }}>选择目光</span>
            </div>
            <Link to="/#composer" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 11, color: '#756e61', textDecoration: 'none' }}>
              <Icon name="pen" size={14} /> 修改我的问题
            </Link>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
              border: '1px solid #cec3b0',
              background: '#f8f3e9',
              marginTop: 28,
            }}
          >
            {['提出问题', '选择目光', '展开对话', '形成记录'].map((label, index) => {
              const active = index === 1
              const done = index === 0
              return (
                <div
                  key={label}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 14px',
                    borderBottom: index < 2 ? '1px solid #d8cdb9' : undefined,
                  }}
                >
                  <span
                    className="font-display"
                    style={{
                      display: 'grid',
                      placeItems: 'center',
                      width: 22,
                      height: 22,
                      borderRadius: 999,
                      border: active ? 'none' : '1px solid #b7ad9b',
                      background: active ? '#304235' : done ? '#304235' : 'transparent',
                      color: active || done ? '#fbf7ef' : '#a09686',
                      fontSize: 10,
                    }}
                  >
                    {done ? <Icon name="check" size={10} /> : String(index + 1).padStart(2, '0')}
                  </span>
                  <span style={{ fontSize: 11, color: active ? '#304235' : index < 2 ? '#7c7568' : '#9a9284', fontWeight: active ? 600 : 400 }}>
                    {label}
                  </span>
                </div>
              )
            })}
          </div>

          <div style={{ display: 'grid', gap: 40, marginTop: 40, gridTemplateColumns: '1fr' }}>
            <div>
              <div className="eyebrow">THREE WAYS OF SEEING</div>
              <h1 className="section-title" style={{ marginTop: 20, fontSize: 40 }}>
                同一个问题，
                <br />
                三种不同的<span style={{ color: '#9b4f35' }}>光。</span>
              </h1>
              <p className="font-display" style={{ marginTop: 24, maxWidth: 520, fontSize: 15, lineHeight: 1.95, color: '#6e675b' }}>
                下面不是三个“正确答案”，而是三种理解处境的入口。它们会把你带向不同的追问，也让你看见自己更愿意站在哪里。
              </p>
            </div>

            <div className="question-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #5c6c5c', paddingBottom: 14 }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 9, fontWeight: 600, letterSpacing: '0.2em', color: '#c7d1c1' }}>
                  <span style={{ width: 6, height: 6, borderRadius: 999, background: '#b08a4b' }} />
                  YOUR QUESTION
                </span>
                <span className="font-display" style={{ fontSize: 12, fontStyle: 'italic', color: '#a4b09e' }}>
                  01
                </span>
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 24 }}>
                <span className="font-display" style={{ fontSize: 34, lineHeight: 1, color: '#b08a4b' }}>
                  “
                </span>
                <p className="font-display" style={{ margin: 0, fontSize: 22, lineHeight: 1.7, color: '#fbf7ef' }}>
                  {session.question}
                </p>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #5c6c5c', marginTop: 32, paddingTop: 14 }}>
                <span style={{ fontSize: 10, letterSpacing: '0.12em', color: '#a8b4a3' }}>问题已被保留</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 10, color: '#d9c7a8' }}>
                  <Icon name="check" size={12} /> READY
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section style={{ borderBottom: '1px solid var(--line)', background: 'var(--paper-soft)' }}>
        <div className="container" style={{ padding: '24px 24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, borderLeft: '2px solid var(--gold)', paddingLeft: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 9, fontWeight: 600, letterSpacing: '0.18em', color: '#8a4b35' }}>
              <Icon name="sparkles" size={14} /> AGENT&apos;S READING
            </div>
            <p className="font-display" style={{ margin: 0, maxWidth: 960, fontSize: 14, lineHeight: 1.9, color: '#5f594e' }}>
              {session.reading}
            </p>
          </div>
        </div>
      </section>

      <section style={{ borderBottom: '1px solid var(--line)' }}>
        <div className="container" style={{ padding: '56px 24px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 32 }}>
            <h2 className="section-title" style={{ fontSize: 31 }}>
              为你浮现的三种目光
            </h2>
            <p style={{ maxWidth: 380, margin: 0, fontSize: 11, lineHeight: 1.9, color: '#8a8375' }}>
              不必选择“最正确”的那一个。选择你此刻最愿意借用、也最可能带来新看见的那一个。
            </p>
          </div>

          <div className="lens-grid">
            {session.perspectives.map((lens, index) => (
              <div key={lens.key} style={{ opacity: selecting && selecting !== lens.key ? 0.45 : 1 }}>
                <LensCard lens={lens} index={index} onSelect={choose} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ borderBottom: '1px solid var(--line)', background: 'var(--paper-soft)' }}>
        <div className="container" style={{ padding: '56px 24px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 32 }}>
            <h2 className="section-title" style={{ fontSize: 30 }}>
              三种目光，在哪里分岔？
            </h2>
            <p style={{ maxWidth: 400, margin: 0, fontSize: 11, lineHeight: 1.85, color: '#8a8375' }}>
              分岔不是为了裁决高下，而是为了让你看清：自己更愿意从哪一个方向开始承担。
            </p>
          </div>

          <div className="compare-table">
            <div className="compare-table__row compare-table__row--head">
              <div className="compare-table__cell" style={{ fontWeight: 600, letterSpacing: '0.14em', color: '#8b8273' }}>
                对照维度
              </div>
              {session.perspectives.map((lens) => (
                <div className="compare-table__cell" key={lens.key}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: lens.accent }}>{lens.name}</div>
                  <div style={{ marginTop: 4, fontSize: 8, letterSpacing: '0.14em', color: '#8a9584' }}>{lens.en}</div>
                </div>
              ))}
            </div>
            {COMPARE.map((row) => (
              <div className="compare-table__row" key={row.dimension}>
                <div className="compare-table__cell" style={{ fontWeight: 500, color: '#4f4d44' }}>
                  {row.dimension}
                </div>
                {row.items.map((item, index) => (
                  <div className="compare-table__cell" key={item} style={{ color: '#6b6559' }}>
                    {session.perspectives[index]?.name ? item : ''}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="quote-band">
        <div className="container quote-band__inner">
          <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            <Icon name="quote" size={22} />
            <div>
              <p className="font-display" style={{ margin: 0, fontSize: 20, lineHeight: 1.7, color: '#f8f2e6' }}>
                选择不是承诺一生，只是决定下一步朝哪里看。
              </p>
              <p style={{ marginTop: 8, fontSize: 10, letterSpacing: '0.14em', color: '#aab7a6' }}>
                YOU CAN ALWAYS CHANGE THE LENS
              </p>
            </div>
          </div>
          <Link to="/" className="btn btn--ghost" style={{ borderColor: '#718070', color: '#e6ddcb' }}>
            换个问题再想想
            <Icon name="arrow-left" size={14} />
          </Link>
        </div>
      </section>
    </>
  )
}
