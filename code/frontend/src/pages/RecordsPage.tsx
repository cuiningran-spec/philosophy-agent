import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Icon } from '../components/Icon'
import type { SessionBrief } from '../types'

function formatDate(iso?: string | null) {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }).format(date)
}

export function RecordsPage() {
  const [sessions, setSessions] = useState<SessionBrief[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .listSessions(30)
      .then(setSessions)
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
  }, [])

  return (
    <div className="container" style={{ padding: '56px 24px' }}>
      <div className="eyebrow">MY THINKING</div>
      <h1 className="section-title" style={{ marginTop: 20, fontSize: 34 }}>
        我的思考
      </h1>
      <p className="font-display" style={{ marginTop: 20, maxWidth: 620, fontSize: 15, lineHeight: 1.95, color: '#6c6558' }}>
        每一次探索都会被保留下来。你可以回到任何一次对话继续追问，也可以重新打开已经生成的思考记录。
      </p>

      {error && <p className="error-text" style={{ marginTop: 20 }}>{error}</p>}

      <div style={{ marginTop: 32, borderTop: '1px solid var(--line)' }}>
        {sessions.length === 0 && !error && <p className="empty-state">还没有开始任何一次探索。</p>}
        {sessions.map((session) => (
          <div
            key={session.id}
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 16,
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--line)',
              padding: '20px 0',
            }}
          >
            <div style={{ minWidth: 0, maxWidth: 640 }}>
              <div style={{ fontSize: 9, letterSpacing: '0.12em', color: '#9a9182' }}>
                {formatDate(session.created_at)} · {session.lens_name || '未选择视角'} · {session.turn_count} 轮追问
              </div>
              <p className="font-display" style={{ margin: '8px 0 0', fontSize: 16, lineHeight: 1.7, color: '#3a3831' }}>
                {session.question}
              </p>
              {session.summary_count > 0 && (
                <span className="chip" style={{ marginTop: 10, borderColor: '#c8d2c1', background: '#eef1e8', color: '#52634e' }}>
                  <Icon name="bookmark" size={10} /> {session.summary_count} 份思考记录
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Link to={`/dialogue/${session.id}`} className="btn btn--ghost" style={{ padding: '8px 14px' }}>
                继续对话
                <Icon name="arrow-right" size={13} />
              </Link>
              {session.summary_count > 0 && (
                <Link to={`/summary/${session.id}`} className="btn" style={{ padding: '8px 14px' }}>
                  查看记录
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
