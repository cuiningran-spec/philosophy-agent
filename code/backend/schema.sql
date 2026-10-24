-- ThinkLab MVP 数据库结构（PostgreSQL）
-- 应用启动时会通过 SQLAlchemy 自动建表；本文件用于评审、迁移与手工建库参考。

CREATE TABLE IF NOT EXISTS sessions (
    id           VARCHAR(36) PRIMARY KEY,
    question     TEXT        NOT NULL,
    lens         VARCHAR(32),
    lens_name    VARCHAR(64),
    core_ask     TEXT,
    rolling_summary TEXT,
    status       VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS perspectives (
    id           VARCHAR(36) PRIMARY KEY,
    session_id   VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    key          VARCHAR(32) NOT NULL,
    name         VARCHAR(64) NOT NULL,
    en           VARCHAR(64) NOT NULL DEFAULT '',
    core_ask     TEXT        NOT NULL DEFAULT '',
    headline     TEXT        NOT NULL DEFAULT '',
    description  TEXT        NOT NULL DEFAULT '',
    quote        TEXT        NOT NULL DEFAULT '',
    thinker      VARCHAR(64) NOT NULL DEFAULT '',
    fit_for      TEXT        NOT NULL DEFAULT '',
    opening      TEXT        NOT NULL DEFAULT '',
    retrieved    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    order_index  INTEGER     NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_perspectives_session ON perspectives(session_id);

CREATE TABLE IF NOT EXISTS messages (
    id          VARCHAR(36) PRIMARY KEY,
    session_id  VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        VARCHAR(16) NOT NULL,
    content     TEXT        NOT NULL,
    turn_index  INTEGER     NOT NULL DEFAULT 0,
    seq         INTEGER     NOT NULL DEFAULT 0,
    sources     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_seq ON messages(session_id, seq);

CREATE TABLE IF NOT EXISTS summaries (
    id          VARCHAR(36) PRIMARY KEY,
    session_id  VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    version     INTEGER     NOT NULL DEFAULT 1,
    question    TEXT        NOT NULL,
    lens        VARCHAR(32) NOT NULL,
    lens_name   VARCHAR(64) NOT NULL,
    core_ask    TEXT        NOT NULL DEFAULT '',
    tagline     TEXT        NOT NULL DEFAULT '',
    turns       INTEGER     NOT NULL DEFAULT 0,
    takeaway    TEXT        NOT NULL DEFAULT '',
    insights    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    tensions    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    practices   JSONB       NOT NULL DEFAULT '[]'::jsonb,
    keywords    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    excerpts    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    sources     JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_summaries_session ON summaries(session_id);

CREATE TABLE IF NOT EXISTS knowledge_docs (
    id        VARCHAR(36) PRIMARY KEY,
    doc_id    VARCHAR(64) UNIQUE NOT NULL,
    title     VARCHAR(255) NOT NULL,
    school    VARCHAR(32) NOT NULL DEFAULT 'general',
    thinker   VARCHAR(64) NOT NULL DEFAULT '',
    kind      VARCHAR(32) NOT NULL DEFAULT 'concept',
    content   TEXT        NOT NULL,
    tags      JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_school ON knowledge_docs(school);

CREATE TABLE IF NOT EXISTS faq_entries (
    id       VARCHAR(36) PRIMARY KEY,
    faq_id   VARCHAR(64) UNIQUE NOT NULL,
    question TEXT NOT NULL,
    answer   TEXT NOT NULL,
    school   VARCHAR(32) NOT NULL DEFAULT 'general',
    tags     JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS retrieval_logs (
    id         VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36),
    query      TEXT NOT NULL,
    school     VARCHAR(32),
    hits       JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_retrieval_session ON retrieval_logs(session_id);
