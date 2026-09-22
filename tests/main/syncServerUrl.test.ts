import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  isOfficialSyncServerUrl,
  LEGACY_OFFICIAL_SYNC_SERVER_URLS,
  normalizeSyncServerUrl,
  OFFICIAL_SYNC_SERVER_URL,
  OFFICIAL_SERVER_HTTP_URL,
  normalizeHttpServerUrl
} from '../../src/shared/syncServerUrl'

describe('syncServerUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('uses HTTPS directly and derives only the sync transport address', () => {
    expect(OFFICIAL_SERVER_HTTP_URL).toBe('https://z-tools.top')
    expect(OFFICIAL_SYNC_SERVER_URL).toBe('wss://z-tools.top')
  })

  it.each([
    ['https://sync.example.com:8443', 'wss://sync.example.com:8443'],
    ['http://[::1]:23517', 'ws://[::1]:23517'],
    ['http://127.0.0.1:23518', 'ws://127.0.0.1:23518'],
    ['https://sync.example.com/', 'wss://sync.example.com'],
    ['ws://localhost:8080/', 'ws://localhost:8080'],
    ['wss://SYNC.EXAMPLE.COM', 'wss://sync.example.com']
  ])('normalizes %s to %s', (input, expected) => {
    expect(normalizeSyncServerUrl(input)).toBe(expected)
  })

  it.each([
    [' https://z-tools.top/ ', 'https://z-tools.top'],
    ['http://127.0.0.1:23517', 'http://127.0.0.1:23517'],
    ['http://localhost:23517', 'http://localhost:23517'],
    ['http://[::1]:23517', 'http://[::1]:23517'],
    ['https://example.com:80', 'https://example.com:80'],
    ['http://localhost:443', 'http://localhost:443'],
    ['https://localhost:23517', 'https://localhost:23517'],
    ['https://192.168.1.10:23517', 'https://192.168.1.10:23517']
  ])('preserves the explicitly configured HTTP protocol for %s', (input, expected) => {
    expect(normalizeHttpServerUrl(input)).toBe(expected)
  })

  it.each([
    ['', '请填写服务器地址'],
    ['ftp://sync.example.com', '仅支持'],
    ['https://user:secret@sync.example.com', '不能包含账号或密码'],
    ['https://sync.example.com/api', '暂不支持子路径'],
    ['https://sync.example.com/?tenant=a', '不能包含查询参数'],
    ['z-tools.top/api', '格式不正确'],
    ['https://z-tools.top#anchor', '不能包含查询参数'],
    ['127.0.0.1:bad', '格式不正确']
  ])('rejects invalid server address %s', (input, message) => {
    expect(() => normalizeSyncServerUrl(input)).toThrow(message)
    expect(() => normalizeHttpServerUrl(input)).toThrow(message)
  })

  it('recognizes the current and trusted legacy official service addresses', () => {
    expect(isOfficialSyncServerUrl('https://z-tools.top/')).toBe(true)
    expect(
      isOfficialSyncServerUrl(`${LEGACY_OFFICIAL_SYNC_SERVER_URLS[0].replace('wss:', 'https:')}/`)
    ).toBe(true)
    expect(isOfficialSyncServerUrl('z-tools.top')).toBe(false)
    expect(isOfficialSyncServerUrl(OFFICIAL_SYNC_SERVER_URL)).toBe(true)
    expect(isOfficialSyncServerUrl('https://private.example.com')).toBe(false)
  })

  it('keeps existing local WS sessions recognized with an HTTP build setting', async () => {
    vi.stubGlobal('__ZTOOLS_OFFICIAL_SYNC_SERVER_URL__', 'http://127.0.0.1:23517')
    vi.resetModules()
    const local = await import('../../src/shared/syncServerUrl')
    expect(local.OFFICIAL_SERVER_HTTP_URL).toBe('http://127.0.0.1:23517')
    expect(local.OFFICIAL_SYNC_SERVER_URL).toBe('ws://127.0.0.1:23517')
    expect(local.isOfficialSyncServerUrl('ws://127.0.0.1:23517')).toBe(true)
    expect(local.isOfficialSyncServerUrl('http://127.0.0.1:23517')).toBe(true)
    expect(local.isOfficialSyncServerUrl('z-tools.top')).toBe(false)
  })

  it.each(['z-tools.top', '127.0.0.1:23517', 'ws://localhost:23517', 'wss://z-tools.top'])(
    'rejects non-HTTP build configuration %s instead of guessing its protocol',
    async (input) => {
      expect(() => normalizeHttpServerUrl(input)).toThrow()
      vi.stubGlobal('__ZTOOLS_OFFICIAL_SYNC_SERVER_URL__', input)
      vi.resetModules()
      await expect(import('../../src/shared/syncServerUrl')).rejects.toThrow()
    }
  )
})
