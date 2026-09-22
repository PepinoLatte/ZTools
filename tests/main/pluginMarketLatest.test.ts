import { beforeEach, describe, expect, it, vi } from 'vitest'

const mockRequestPluginMarket = vi.hoisted(() => vi.fn())

vi.mock('../../src/main/api/renderer/pluginMarketConfig', () => ({
  PluginMarketAuthRequiredError: class PluginMarketAuthRequiredError extends Error {},
  PluginMarketAuthMode: { OPTIONAL: 'optional', REQUIRED: 'required' },
  getPluginMarketApiBase: () => 'https://z-tools.top/api/market',
  requestPluginMarket: mockRequestPluginMarket
}))

vi.mock('../../src/main/utils/httpRequest.js', () => ({
  httpGet: vi.fn()
}))

vi.mock('../../src/main/api/shared/database', () => ({
  default: {
    dbGet: vi.fn(),
    dbPut: vi.fn()
  }
}))

import { PluginMarketAPI } from '../../src/main/api/renderer/pluginMarket'

describe('PluginMarketAPI.fetchLatestPlugin', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('deduplicates concurrent requests and reuses the positive cache', async () => {
    let resolveRequest: ((value: any) => void) | undefined
    mockRequestPluginMarket.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      })
    )
    const api = new PluginMarketAPI()

    const first = api.fetchLatestPlugin('demo', 'darwin')
    const second = api.fetchLatestPlugin('demo', 'darwin')

    expect(mockRequestPluginMarket).toHaveBeenCalledTimes(1)
    resolveRequest?.({
      status: 200,
      data: {
        available: true,
        plugin: { name: 'demo', title: 'Demo', version: '1.2.0' }
      }
    })

    await expect(first).resolves.toMatchObject({
      available: true,
      plugin: { name: 'demo', version: '1.2.0' }
    })
    await expect(second).resolves.toMatchObject({ available: true })
    await expect(api.fetchLatestPlugin('demo', 'darwin')).resolves.toMatchObject({
      available: true
    })
    expect(mockRequestPluginMarket).toHaveBeenCalledTimes(1)
  })

  it('returns a normal unavailable result for an unlisted plugin', async () => {
    mockRequestPluginMarket.mockResolvedValue({
      status: 200,
      data: { available: false, reason: 'not_found' }
    })
    const api = new PluginMarketAPI()

    await expect(api.fetchLatestPlugin('local-only', 'win32')).resolves.toEqual({
      available: false,
      reason: 'not_found'
    })
  })
})

describe('PluginMarketAPI.fetchReleaseHistory', () => {
  beforeEach(() => vi.clearAllMocks())

  it('uses the configured market endpoint and forwards pagination', async () => {
    mockRequestPluginMarket.mockResolvedValue({
      status: 200,
      data: JSON.stringify({ name: 'demo', currentVersion: '2.0.0', items: [], nextOffset: 40 })
    })
    await expect(new PluginMarketAPI().fetchReleaseHistory(' demo ', 20)).resolves.toMatchObject({
      currentVersion: '2.0.0',
      nextOffset: 40
    })
    expect(mockRequestPluginMarket).toHaveBeenCalledWith(
      '/plugins/releases?name=demo&limit=20&offset=20'
    )
  })

  it('rejects invalid input and invalid responses', async () => {
    const api = new PluginMarketAPI()
    await expect(api.fetchReleaseHistory('')).rejects.toThrow()
    await expect(api.fetchReleaseHistory('demo', -1)).rejects.toThrow()
    expect(mockRequestPluginMarket).not.toHaveBeenCalled()
    mockRequestPluginMarket.mockResolvedValue({ status: 200, data: {} })
    await expect(api.fetchReleaseHistory('demo')).rejects.toThrow('更新日志响应无效')
  })
})
