/**
 * ThinkLab Node.js Web 服务（BFF）
 *  - 托管 React 构建产物 dist/
 *  - 把 /api 反向代理到 FastAPI 智能体服务（支持 SSE 流式透传）
 *
 * 启动：node server/index.mjs
 * 环境变量：PORT（默认 4173）、AGENT_API_BASE（默认 http://127.0.0.1:8000）
 */
import express from 'express'
import path from 'node:path'
import { Readable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DIST = path.resolve(__dirname, '..', 'dist')
const PORT = Number(process.env.PORT || 4173)
const AGENT_API_BASE = process.env.AGENT_API_BASE || 'http://127.0.0.1:8000'

const app = express()

/** 收集请求体（GET/HEAD 无 body） */
async function readBody(req) {
  if (req.method === 'GET' || req.method === 'HEAD') return undefined
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  return Buffer.concat(chunks)
}

app.use('/api', async (req, res) => {
  const target = `${AGENT_API_BASE}${req.originalUrl}`
  const headers = { ...req.headers }
  delete headers.host
  delete headers['content-length']
  delete headers['accept-encoding']

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body: await readBody(req),
      redirect: 'manual',
    })
    res.status(upstream.status)
    upstream.headers.forEach((value, key) => {
      if (['transfer-encoding', 'content-length', 'connection'].includes(key)) return
      res.setHeader(key, value)
    })
    if (upstream.body) {
      await pipeline(Readable.fromWeb(upstream.body), res)
    } else {
      res.end()
    }
  } catch (error) {
    res.status(502).json({ detail: `无法连接智能体服务 ${AGENT_API_BASE}：${error.message}` })
  }
})

app.use(express.static(DIST, { index: false, maxAge: '1h' }))

// SPA 回退
app.get('*', (_req, res) => {
  res.sendFile(path.join(DIST, 'index.html'))
})

app.listen(PORT, () => {
  console.log(`[thinklab-web] http://localhost:${PORT}  →  agent: ${AGENT_API_BASE}`)
})
