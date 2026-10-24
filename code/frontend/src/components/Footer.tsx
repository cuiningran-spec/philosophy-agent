export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__inner">
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 24,
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid #d3c8b5',
            paddingBottom: 24,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span
              className="font-display"
              style={{
                display: 'grid',
                placeItems: 'center',
                width: 40,
                height: 40,
                border: '1px solid #3a3931',
                fontSize: 18,
              }}
            >
              思
            </span>
            <div>
              <div className="font-display" style={{ fontSize: 17 }}>
                ThinkLab
              </div>
              <div style={{ marginTop: 4, fontSize: 9, letterSpacing: '0.2em', color: '#8a8375' }}>
                哲学思考实验室
              </div>
            </div>
          </div>
          <p className="font-display" style={{ margin: 0, fontStyle: 'italic', color: '#7b7467', fontSize: 13 }}>
            慢一点，但更深一点。
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 12,
            flexWrap: 'wrap',
            paddingTop: 18,
            fontSize: 9,
            color: '#978f81',
          }}
        >
          <span>© 2026 ThinkLab. A quiet place for difficult questions.</span>
          <span>ThinkLab 提供思考路径，不替你做决定。</span>
        </div>
      </div>
    </footer>
  )
}
