// 把剪贴板插件的 pindata/pinscreen 特征码同步进插件注册表，并清指令缓存
const path = require('path')
const os = require('os')
const { createRequire } = require('module')
const req = createRequire(
  path.join(process.env.USERPROFILE, '.ztools-autopin', 'tools', 'package.json')
)
const lmdb = req('lmdb')
;(async () => {
  const env = lmdb.open({
    path: path.join(os.homedir(), '.ztools', 'lmdb', 'device'),
    mapSize: 2 * 1024 * 1024 * 1024,
    maxDbs: 6,
    compression: false,
    encoding: 'binary'
  })
  const db = env.openDB({ name: 'main', encoding: 'string' })
  const get = (id) => {
    const r = db.get(id)
    return r ? JSON.parse(r.toString('utf8')) : null
  }
  const doc = get('ZTOOLS/plugins')
  if (!doc || !Array.isArray(doc.data)) throw new Error('plugins registry not found')
  const clip = doc.data.find((p) => p && p.name === 'clipboard')
  if (!clip) throw new Error('clipboard plugin not found in registry')
  const codes = (clip.features || []).map((f) => f.code)
  const logo = clip.logo || ''
  if (!codes.includes('pinscreen')) {
    clip.features.push({
      code: 'pinscreen',
      explain: '剪贴板以小窗口模式悬浮屏幕上',
      cmds: ['悬浮剪贴板', '悬浮剪切板'],
      icon: logo
    })
    console.log('registry: + pinscreen')
  }
  if (!codes.includes('pindata')) {
    clip.features.push({
      code: 'pindata',
      explain: '内容加固定到悬浮屏幕的临时中转站',
      cmds: [
        { type: 'over', label: '文本悬浮中转' },
        { type: 'img', label: '图像悬浮中转' },
        { type: 'files', label: '文件悬浮中转' }
      ],
      icon: logo
    })
    console.log('registry: + pindata')
  }
  const put = (id, data, rev) => {
    const d = { _id: id, data }
    if (rev) d._rev = rev
    db.put(id, JSON.stringify(d))
  }
  put('ZTOOLS/plugins', doc.data, doc._rev)
  // 清指令缓存，强制重建（含新特征码）
  for (const k of ['ZTOOLS/cached-commands', 'ZTOOLS/cached-commands-version']) {
    if (db.get(k)) {
      db.remove(k)
      console.log('cleared', k)
    }
  }
  await env.close()
  console.log('registry updated')
})().catch((e) => {
  console.error(e)
  process.exit(1)
})
