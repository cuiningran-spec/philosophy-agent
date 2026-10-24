import { Icon } from './Icon'
import type { Lens, Message } from '../types'

function formatTime(iso?: string | null) {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

interface Props {
  message: Message
  lens?: Lens | null
  streaming?: boolean
}

export function MessageBubble({ message, lens, streaming }: Props) {
  const isUser = message.role === 'user'
  const accent = lens?.accent || '#43563f'

  if (isUser) {
    return (
      <div className="message message--user">
        <div className="message__body">
          <div className="message__meta">
            <span>{formatTime(message.created_at)}</span>
            <span style={{ fontWeight: 500, color: '#8a6a5b' }}>你</span>
          </div>
          <div className="message__bubble">
            <p className="message__text">{message.content}</p>
          </div>
        </div>
        <div className="message__avatar message__avatar--user">你</div>
      </div>
    )
  }

  return (
    <div className="message">
      <div className="message__avatar" style={{ background: accent }}>
        <span className="font-display">思</span>
      </div>
      <div className="message__body">
        <div className="message__meta">
          <span style={{ fontWeight: 500, color: '#777064' }}>哲学 Agent</span>
          <span style={{ color: accent }}>{lens?.name || 'ThinkLab'}</span>
          <span style={{ marginLeft: 'auto' }}>{formatTime(message.created_at)}</span>
        </div>
        <div className="message__bubble" style={{ borderLeftColor: accent }}>
          <p className="message__text">
            {message.content}
            {streaming && <span className="spinner-line" style={{ marginLeft: 6 }} />}
          </p>
          {message.sources.length > 0 && (
            <div className="message__sources">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <Icon name="search" size={11} /> 检索语料
              </span>
              <span style={{ marginLeft: 6 }}>
                {message.sources.map((s) => s.title).join(' · ')}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function TypingIndicator({ accent }: { accent: string }) {
  return (
    <div className="message">
      <div className="message__avatar" style={{ background: accent }}>
        <span className="font-display">思</span>
      </div>
      <div className="message__bubble" style={{ borderLeftColor: accent, padding: '12px 16px' }}>
        <span className="typing">
          <span />
          <span />
          <span />
        </span>
        <span style={{ marginLeft: 10, fontSize: 11, color: '#9b9284' }}>正在顺着这个视角思考</span>
      </div>
    </div>
  )
}
