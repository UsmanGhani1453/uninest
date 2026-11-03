import { timingSafeEqual } from 'node:crypto'
import { createReadStream } from 'node:fs'
import { stat } from 'node:fs/promises'
import { createServer, request as proxyRequest } from 'node:http'
import { extname, isAbsolute, relative, resolve } from 'node:path'

const port = Number(process.env.STAGING_GATEWAY_PORT ?? 5176)
const distDirectory = resolve(process.env.STAGING_FRONTEND_DIST ?? 'dist')
const stagingPassword = process.env.STAGING_GATEWAY_PASSWORD ?? ''
const sessionToken = process.env.STAGING_GATEWAY_SESSION_TOKEN ?? ''
const cookieName = 'uninest_staging'
const maxAttempts = 8
const lockoutMs = 15 * 60 * 1000
const attempts = { count: 0, resetAt: 0, blockedUntil: 0 }

if (stagingPassword.length < 24 || sessionToken.length < 32) {
  throw new Error('Provide a long staging password and a random session token.')
}

const loginPage = (message = '') => `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>Private UniNest test</title>
</head>
<body>
  <main>
    <h1>Private UniNest test</h1>
    <p>Enter the invitation password to continue.</p>
    ${message ? `<p role="alert">${message}</p>` : ''}
    <form method="post" action="/__gate">
      <label for="password">Invitation password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Continue</button>
    </form>
  </main>
</body>
</html>`

function respond(response, status, body, headers = {}) {
  response.writeHead(status, {
    'Cache-Control': 'no-store',
    'Content-Type': 'text/html; charset=utf-8',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-Robots-Tag': 'noindex, nofollow',
    ...headers,
  })
  response.end(body)
}

function safeEqual(left, right) {
  const leftBuffer = Buffer.from(left)
  const rightBuffer = Buffer.from(right)
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer)
}

function hasSession(request) {
  const cookieHeader = request.headers.cookie ?? ''
  return cookieHeader.split(';').some((part) => {
    const separator = part.indexOf('=')
    return separator > 0
      && part.slice(0, separator).trim() === cookieName
      && safeEqual(part.slice(separator + 1).trim(), sessionToken)
  })
}

function readPassword(request) {
  return new Promise((resolveBody, rejectBody) => {
    let body = ''
    request.setEncoding('utf8')
    request.on('data', (chunk) => {
      body += chunk
      if (body.length > 4096) {
        rejectBody(new Error('Request body is too large.'))
        request.destroy()
      }
    })
    request.on('end', () => resolveBody(new URLSearchParams(body).get('password') ?? ''))
    request.on('error', rejectBody)
  })
}

async function serveFile(request, response, pathname) {
  let decodedPath
  try {
    decodedPath = decodeURIComponent(pathname)
  } catch {
    respond(response, 400, 'Invalid path.')
    return
  }

  let filePath = resolve(distDirectory, `.${decodedPath}`)
  const fileRelativePath = relative(distDirectory, filePath)
  if (fileRelativePath.startsWith('..') || isAbsolute(fileRelativePath)) {
    respond(response, 400, 'Invalid path.')
    return
  }

  try {
    if (!(await stat(filePath)).isFile()) {
      filePath = resolve(distDirectory, 'index.html')
    }
  } catch {
    filePath = resolve(distDirectory, 'index.html')
  }

  const contentType = {
    '.css': 'text/css; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.ico': 'image/x-icon',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
  }[extname(filePath).toLowerCase()] ?? 'application/octet-stream'

  response.writeHead(200, {
    'Cache-Control': 'no-store',
    'Content-Type': contentType,
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-Robots-Tag': 'noindex, nofollow',
  })
  if (request.method === 'HEAD') {
    response.end()
    return
  }
  createReadStream(filePath).pipe(response)
}

const server = createServer(async (request, response) => {
  const pathname = new URL(request.url ?? '/', 'http://localhost').pathname

  if (pathname === '/__gate' && request.method === 'GET') {
    if (hasSession(request)) {
      response.writeHead(303, { Location: '/' })
      response.end()
      return
    }
    respond(response, 200, loginPage(), {
      'Content-Security-Policy': "default-src 'none'; form-action 'self'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
    })
    return
  }

  if (pathname === '/__gate' && request.method === 'POST') {
    const now = Date.now()
    if (attempts.blockedUntil > now) {
      respond(response, 429, loginPage('Too many attempts. Try again later.'), {
        'Retry-After': String(Math.ceil((attempts.blockedUntil - now) / 1000)),
      })
      return
    }
    if (attempts.resetAt < now) {
      attempts.count = 0
      attempts.resetAt = now + lockoutMs
    }

    try {
      const submittedPassword = await readPassword(request)
      if (safeEqual(submittedPassword, stagingPassword)) {
        attempts.count = 0
        response.writeHead(303, {
          'Cache-Control': 'no-store',
          'Location': '/',
          'Set-Cookie': `${cookieName}=${sessionToken}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=28800`,
        })
        response.end()
        return
      }
      attempts.count += 1
      if (attempts.count >= maxAttempts) {
        attempts.blockedUntil = now + lockoutMs
      }
      respond(response, 401, loginPage('That invitation password was not accepted.'), {
        'Content-Security-Policy': "default-src 'none'; form-action 'self'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
      })
    } catch (error) {
      respond(response, 413, 'Request body is too large.')
    }
    return
  }

  if (pathname === '/__logout' && request.method === 'POST' && hasSession(request)) {
    response.writeHead(303, {
      'Cache-Control': 'no-store',
      'Location': '/__gate',
      'Set-Cookie': `${cookieName}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0`,
    })
    response.end()
    return
  }

  if (!hasSession(request)) {
    response.writeHead(303, { 'Cache-Control': 'no-store', Location: '/__gate' })
    response.end()
    return
  }

  if (pathname.startsWith('/api/')) {
    const upstream = proxyRequest({
      hostname: '127.0.0.1',
      port: 8001,
      method: request.method,
      path: request.url,
      headers: { ...request.headers, host: '127.0.0.1:8001' },
    }, (upstreamResponse) => {
      response.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers)
      upstreamResponse.pipe(response)
    })
    upstream.on('error', () => {
      if (!response.headersSent) {
        respond(response, 502, 'The staging API is unavailable.')
      } else {
        response.destroy()
      }
    })
    request.pipe(upstream)
    return
  }

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    respond(response, 405, 'Method not allowed.')
    return
  }
  await serveFile(request, response, pathname)
})

server.on('error', (error) => {
  console.error('Staging gateway failed:', error.message)
  process.exitCode = 1
})

server.listen(port, '127.0.0.1', () => {
  console.log(`Private staging gateway listening on 127.0.0.1:${port}`)
})
