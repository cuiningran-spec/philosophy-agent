import { Icon } from './Icon'
import type { Lens } from '../types'

const ICON_BY_KEY: Record<string, 'columns' | 'compass' | 'waves'> = {
  stoic: 'columns',
  existential: 'compass',
  taoist: 'waves',
}

interface Props {
  lens: Lens
  index: number
  selected?: boolean
  onSelect?: (lens: Lens) => void
}

export function LensCard({ lens, index, selected, onSelect }: Props) {
  return (
    <article
      className="lens-card"
      style={{
        borderColor: lens.line,
        background: lens.soft,
        opacity: selected ? 1 : undefined,
      }}
    >
      <span className="lens-card__num">{String(index + 1).padStart(2, '0')}</span>

      <div style={{ position: 'relative', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <span
          className="lens-card__icon"
          style={{ borderColor: lens.line, background: '#fff', color: lens.accent }}
        >
          <Icon name={ICON_BY_KEY[lens.key] || 'compass'} size={22} />
        </span>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 9, fontWeight: 600, letterSpacing: '0.19em', color: lens.accent }}>
            {lens.en}
          </div>
          <div className="font-display" style={{ marginTop: 4, fontSize: 12, fontStyle: 'italic', opacity: 0.8 }}>
            LENS {['I', 'II', 'III'][index] || index + 1}
          </div>
        </div>
      </div>

      <div className="lens-card__ask" style={{ borderColor: lens.line }}>
        <div style={{ fontSize: 10, letterSpacing: '0.13em', color: lens.accent }}>它首先会问</div>
        <h3 className="lens-card__headline" style={{ color: lens.accent }}>
          {lens.headline.split('\n').map((line) => (
            <span key={line} style={{ display: 'block' }}>
              {line}
            </span>
          ))}
        </h3>
        <p className="lens-card__desc" style={{ color: '#667061' }}>
          {lens.description}
        </p>
      </div>

      <div style={{ position: 'relative', flex: 1 }}>
        <figure className="quote-block" style={{ borderColor: lens.line }}>
          <blockquote
            className="font-display"
            style={{ margin: 0, fontSize: 13, lineHeight: 1.8, color: '#5b6858' }}
          >
            “{lens.quote}”
          </blockquote>
          <figcaption style={{ marginTop: 8, fontSize: 9, letterSpacing: '0.12em', color: '#899583' }}>
            {lens.thinker}
          </figcaption>
        </figure>

        <div className="lens-card__meta" style={{ borderColor: lens.line }}>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', opacity: 0.75 }}>适合当你</div>
            <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.75, color: '#5d685a' }}>{lens.fit_for}</div>
          </div>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', opacity: 0.75 }}>思想线索</div>
            <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.75, color: '#5d685a' }}>
              {lens.thinkers.join(' · ')}
            </div>
          </div>
        </div>
      </div>

      {onSelect && (
        <button
          type="button"
          className="btn btn--block"
          style={{ marginTop: 26, background: lens.accent, borderColor: lens.accent }}
          onClick={() => onSelect(lens)}
        >
          <span>借这个视角继续</span>
          <Icon name="arrow-up-right" size={17} />
        </button>
      )}
    </article>
  )
}
