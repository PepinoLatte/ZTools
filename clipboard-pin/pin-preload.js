// 剪贴板悬浮中转子窗口 preload：提供 fs 拖出转换与父窗口数据接收桥
const fs = require('fs')
const path = require('path')
const os = require('os')
const { ipcRenderer } = require('electron')

const tempRoot = path.join(os.tmpdir(), 'ztools-clipboard-pin')

// 把钉住的内容转换为可拖出的临时文件路径（对标 uTools convertDragFiles）
function toDragFiles(items) {
  try {
    fs.mkdirSync(tempRoot, { recursive: true })
  } catch {}
  const out = []
  for (const it of items || []) {
    if (!it) continue
    if (it.type === 'files') {
      for (const f of it.value || []) {
        try {
          if (f && f.path && fs.existsSync(f.path)) out.push(f.path)
        } catch {}
      }
      continue
    }
    if (it.type === 'text') {
      try {
        const p = path.join(tempRoot, 'pin-' + it.timestamp + '.txt')
        if (!fs.existsSync(p)) fs.writeFileSync(p, it.value || '', 'utf-8')
        out.push(p)
      } catch {}
      continue
    }
    if (it.type === 'image') {
      try {
        const p = path.join(tempRoot, 'pin-' + it.timestamp + '.png')
        if (!fs.existsSync(p)) {
          if (/^data:image\/([a-z]+);base64,/.test(it.value || '')) {
            fs.writeFileSync(
              p,
              Buffer.from(it.value.replace(/^data:image\/([a-z]+);base64,/, ''), 'base64')
            )
          } else if (it.value && fs.existsSync(it.value)) {
            fs.copyFileSync(it.value, p)
          } else {
            continue
          }
        }
        out.push(p)
      } catch {}
      continue
    }
  }
  return out
}

window.__pinBridge = {
  toDragFiles,
  onData: (cb) =>
    ipcRenderer.on('zt-pin-data', (_e, data) => {
      try {
        cb(data)
      } catch {}
    })
}
