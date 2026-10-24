interface Props {
  current: 1 | 2 | 3 | 4
  viewName?: string | null
  turns?: number
  hasSummary?: boolean
  stale?: boolean
}

const LABELS = ['提出问题', '选择目光', '展开对话', '形成记录']

export function Steps({ current, viewName, turns = 0, hasSummary, stale }: Props) {
  const states = [
    '已保留你的原始表述',
    viewName || '尚未选择',
    turns > 0 ? `已留下 ${turns} 次追问` : '正在这条视角里深入',
    hasSummary ? (stale ? '已有新对话，可更新记录' : '记录已形成，仍可继续') : '随时可以生成总结',
  ]

  return (
    <div className="journey">
      {LABELS.map((label, index) => {
        const step = index + 1
        const done = step < current || (step === 4 && hasSummary && !stale)
        const active = step === current
        return (
          <div className="journey__item" key={label}>
            <span
              className={`journey__dot${done ? ' journey__dot--done' : ''}${active ? ' journey__dot--active' : ''}`}
            />
            <div style={{ fontSize: 12, fontWeight: 500, color: active ? '#34332d' : done ? '#59554b' : '#8a8274' }}>
              {label}
            </div>
            <div style={{ marginTop: 4, fontSize: 10, lineHeight: 1.6, color: '#8a8274' }}>{states[index]}</div>
          </div>
        )
      })}
    </div>
  )
}
