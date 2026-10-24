import { useEffect, useRef, useState } from 'react'
import { Icon } from './Icon'

interface Props {
  placeholder?: string
  chips?: string[]
  disabled?: boolean
  busy?: boolean
  hint?: string
  onSubmit: (text: string) => void
}

export function Composer({ placeholder, chips = [], disabled, busy, hint, onSubmit }: Props) {
  const [value, setValue] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 132)}px`
  }, [value])

  const submit = () => {
    const text = value.trim()
    if (!text || disabled || busy) return
    setValue('')
    onSubmit(text)
  }

  return (
    <div className="composer-bar__inner">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 11 }}>
        <span style={{ fontWeight: 600, letterSpacing: '0.16em', color: '#8e8678' }}>FOLLOW UP / 继续追问</span>
        <span style={{ color: '#9c9384' }}>{hint || 'Enter 发送 · Shift + Enter 换行'}</span>
      </div>

      {chips.length > 0 && (
        <div className="prompt-chips">
          {chips.map((chip) => (
            <button key={chip} type="button" className="prompt-chip" onClick={() => setValue(chip)}>
              {chip}
            </button>
          ))}
        </div>
      )}

      <div className="field" style={{ padding: 6 }}>
        <textarea
          ref={ref}
          className="field-input"
          rows={2}
          value={value}
          disabled={disabled}
          placeholder={placeholder || '写下此刻想到的第一句话…'}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              submit()
            }
          }}
        />
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            borderTop: '1px solid #e3dacb',
            padding: '8px 8px 2px',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#a09787' }}>
            <Icon name="shield" size={12} /> 可随时生成总结，也可继续对话
          </span>
          <button type="button" className="btn" disabled={disabled || busy} onClick={submit}>
            发送
            <Icon name="arrow-up" size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}
