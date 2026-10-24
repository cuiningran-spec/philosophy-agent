import { Link, NavLink } from 'react-router-dom'

export function Header() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link to="/" className="brand" aria-label="ThinkLab 首页">
          <span className="brand__mark font-display">思</span>
          <span>
            <span className="brand__name" style={{ display: 'block' }}>
              ThinkLab
            </span>
            <span className="brand__sub">哲学思考实验室</span>
          </span>
        </Link>

        <nav className="site-nav" aria-label="主导航">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'is-active' : '')}>
            开始探索
          </NavLink>
          <a href="/#method">思考方法</a>
          <NavLink to="/records" className={({ isActive }) => (isActive ? 'is-active' : '')}>
            我的思考
          </NavLink>
          <NavLink to="/faq" className={({ isActive }) => (isActive ? 'is-active' : '')}>
            知识库问答
          </NavLink>
        </nav>

        <Link to="/#composer" className="btn btn--ghost" style={{ padding: '8px 14px' }}>
          写下问题
        </Link>
      </div>
    </header>
  )
}
