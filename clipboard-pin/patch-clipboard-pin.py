#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板插件「悬浮中转 + 悬浮剪贴板」补丁 v2（对标 uTools 剪贴板 v4.3.2，可重复执行）
------------------------------------------
基于 uTools 官方剪贴板插件逆向行为，给 ZTools 剪贴板插件补齐：

  1. 侧边栏「悬浮中转」图钉按钮：置顶悬浮中转站窗口（无需先选中，自动钉当前活动记录）
  2. 右键菜单新增「悬浮中转」：钉住任意一条记录
  3. 中转站窗口（pindata）：常驻复用、右下角 360px、内容累积、collect/<hash> 持久化、
     每条可 复制/拖出/删除，支持清空；文本/图片/文件全类型
  4. 「悬浮剪贴板」窗口（pinscreen）：实时历史流，点击记录=复制并粘贴
  5. 新增特征码：pindata（文本/图像/文件悬浮中转 over/img/files 匹配）
     与 pinscreen（关键词 悬浮剪贴板/悬浮剪切板）
  6. pin-preload.js：子窗口 fs 桥（内容转临时文件拖出）+ 父窗口数据接收

ZTools / 插件升级覆盖后重新运行本脚本即可：
  python "%USERPROFILE%\\.ztools-autopin\\clipboard-pin\\patch-clipboard-pin.py"
回滚：plugins 目录 clipboard-1.3.2-a0321049.asar.pre-pin.bak 复制回原文件
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOME = os.path.expanduser("~")
PLUGINS = os.path.join(HOME, ".ztools", "plugins")
ASAR = os.path.join(PLUGINS, "clipboard-1.3.2-a0321049.asar")
BACKUP = ASAR + ".pre-pin.bak"
ORIG = os.path.join(HOME, ".ztools-autopin", "clipboard-pin", "clipboard-orig.bak")
ASSETS = os.path.join(HOME, ".ztools-autopin", "clipboard-pin")
MARKER = "[zt-pin]"
TOOL_ASAR = os.path.join(HOME, ".ztools-autopin", "tools", "node_modules", "@electron", "asar", "lib", "asar.js")


def find_bundle(root):
    p = os.path.join(root, "assets", "index-D6-6Wwwu.js")
    if os.path.exists(p):
        return p
    assets = os.path.join(root, "assets")
    best, best_size = None, -1
    for f in os.listdir(assets):
        if f.startswith("index-") and f.endswith(".js"):
            fp = os.path.join(assets, f)
            sz = os.path.getsize(fp)
            if sz > best_size:
                best, best_size = fp, sz
    return best


def rep(src, old, new, expect=1):
    n = src.count(old)
    if n != expect:
        raise SystemExit(f"补丁点异常（匹配 {n} 处，期望 {expect}）：{old[:80]}")
    return src.replace(old, new)


ZTPIN_FUNCS = '''function ztHash(s){let h=5381;for(let i=0;i<s.length;i++){h=((h<<5)+h+s.charCodeAt(i))|0}return (h>>>0).toString(16)+"-"+String(s.length)}
function ztNormalizeRecord(M){const t=M.type;if(!t)return null;const ts=M.timestamp||Date.now();
if(t==="text"){const v=String(M.content??M.value??"" );return {type:"text",value:v,hash:ztHash(v),timestamp:ts}}
if(t==="image"){const v=M.imagePath||String(M.value||"").replace(/^file:\\/\\//,"")||"";if(!v)return null;return {type:"image",value:v,hash:ztHash(v+ts),timestamp:ts,size:M.size}}
if(t==="file"||t==="files"){let arr=[];if(Array.isArray(M.files))arr=M.files.map(f=>f&&f.path?{name:f.name||f.path.split(/[\\\\/]/).pop(),path:f.path,isFile:f.isFile,isDirectory:f.isDirectory}:{name:String(f).split(/[\\\\/]/).pop(),path:String(f),isFile:!0,isDirectory:!1});if(!arr.length)return null;return {type:"files",value:arr,hash:ztHash(JSON.stringify(arr)),timestamp:ts}}
return null}
async function ztPinItem(M){try{const z=window.ztools;if(!z.createBrowserWindow){z.showToast&&z.showToast("当前版本不支持悬浮中转");return}
const rec=ztNormalizeRecord(M);if(!rec){z.showToast&&z.showToast("该记录无法钉住");return}
if(window.__ztPinWin&&!window.__ztPinWin.isDestroyed()){window.__ztPinWin.setAlwaysOnTop(true);window.__ztPinWin.webContents.send("zt-pin-data",[rec]);return}
const disp=z.getDisplayNearestPoint(z.getCursorScreenPoint());const h=Math.round(0.65*disp.workArea.height);
const x=Math.round(disp.workArea.x+disp.workArea.width-360-20);const y=Math.round(disp.workArea.y+disp.workArea.height-h);
window.__ztPinWin=z.createBrowserWindow("pin.html?way=pindata",{show:false,frame:false,focusable:false,fullscreenable:false,minimizable:false,maximizable:false,alwaysOnTop:true,x:x,y:y,width:360,height:h,minWidth:320,maxWidth:600,minHeight:200,transparent:true,backgroundColor:"#00000000",hasShadow:true,webPreferences:{preload:"pin-preload.js"}},()=>{window.__ztPinWin&&window.__ztPinWin.webContents.send("zt-pin-data",[rec]);window.__ztPinWin&&window.__ztPinWin.showInactive()})}catch(e){console.error("[zt-pin] 悬浮中转失败:",e);window.ztools.showToast&&window.ztools.showToast("悬浮中转失败")}}
function ztOpenPinScreen(){try{const z=window.ztools;if(!z.createBrowserWindow)return;
if(window.__ztPinWin&&!window.__ztPinWin.isDestroyed()){window.__ztPinWin.setAlwaysOnTop(true);window.__ztPinWin.webContents.send("zt-pin-way","pinscreen");return}
const disp=z.getDisplayNearestPoint(z.getCursorScreenPoint());const h=Math.round(0.65*disp.workArea.height);
const x=Math.round(disp.workArea.x+disp.workArea.width-360-20);const y=Math.round(disp.workArea.y+disp.workArea.height-h);
window.__ztPinWin=z.createBrowserWindow("pin.html?way=pinscreen",{show:false,frame:false,focusable:false,fullscreenable:false,minimizable:false,maximizable:false,alwaysOnTop:true,x:x,y:y,width:360,height:h,minWidth:320,maxWidth:600,minHeight:200,transparent:true,backgroundColor:"#00000000",hasShadow:true,webPreferences:{preload:"pin-preload.js"}},()=>{window.__ztPinWin&&window.__ztPinWin.showInactive()})}catch(e){console.error("[zt-pin] 悬浮剪贴板失败:",e)}}
function ztEnterPin(E){try{const t=E.type,p=E.payload;
if(t==="over"){if(p)return ztPinItem({type:"text",content:p});return}
if(t==="img"){if(!p)return;if(/^data:image\\//.test(p))return ztPinItem({type:"image",value:p,size:null});
const ts=Date.now();return ztPinItem({type:"image",imagePath:p.replace(/^file:\\/\\//,""),timestamp:ts})}
if(t==="files"){if(!Array.isArray(p))return;return ztPinItem({type:"files",files:p.map(f=>String(f))})}}catch(e){console.error("[zt-pin] enter pin failed:",e)}}
function Nl('''


def patch_bundle(bundle):
    src = open(bundle, encoding="utf-8").read()
    if MARKER in src and "ztOpenPinScreen" in src:
        print("bundle 已是 v2 补丁。")
        return

    # ── 若存在 v1 补丁痕迹，先剥离（从原始逻辑重新打）──
    # v1 注入的模块函数（function ztPinItem ... function Nl）
    if "function ztPinItem(" in src:
        start = src.find("function ztPinItem(")
        end = src.find("function Nl(", start)
        src = src[:start] + src[end:]
    src = rep(src, 'emits:["copy","paste","pin","clear"]', 'emits:["copy","paste","clear"]', expect=0) if src.count('emits:["copy","paste","pin","clear"]') else src
    src = rep(src, 'emits:["copy","paste","pin","clear"]', 'emits:["copy","paste","clear"]', expect=0) if False else src
    # 上面两行合并处理 v1 emits
    v1_btn = src.count('class:"sidebar-btn pin-btn"')
    if v1_btn:
        # 移除 v1 按钮（含其前导逗号）
        start = src.find(',w("button",{class:"sidebar-btn pin-btn"')
        # 找到该 button 元素结尾：其后第一个 "])])" 之后的逗号位置——直接定位到 '])]),w("div",oa,[' 锚点
        end = src.find(']),w("div",oa,[', start)
        assert end > 0
        src = src[:start] + src[end + 1:]

    # ── v2 正式补丁 ──
    # 1) SideBar emits + 图钉按钮（不再置灰）
    src = rep(src, 'emits:["copy","paste","clear"]', 'emits:["copy","paste","pin","clear"]')
    pin_btn = (
        ',w("button",{class:"sidebar-btn pin-btn",'
        'onClick:s[6]||(s[6]=r=>n("pin")),'
        '"data-tooltip":"悬浮中转"},'
        '[w("svg",{viewBox:"0 0 24 24",fill:"none",xmlns:"http://www.w3.org/2000/svg"},'
        '[w("path",{d:"M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3v2h5.97v7l1 1 1-1v-7H18v-2c-1.66 0-3-1.34-3-3z",fill:"currentColor"})])])'
    )
    src = rep(src, ':ce("",!0)],8,na)]),w("div",oa,[', ':ce("",!0)],8,na)' + pin_btn + ']),w("div",oa,[')

    # 2) Nl 返回 pinSelected：优先当前活动记录，其次选中第一条，再退回首条
    src = rep(
        src,
        "return{activeIndex:d,selectedItems:u,",
        "return{pinSelected:async()=>{const M=r.value||u.value[0]||e.value[0];if(!M){window.ztools.showToast&&window.ztools.showToast(\"暂无可固定的记录\");return}await ztPinItem(M)},activeIndex:d,selectedItems:u,",
    )

    # 3) 解构 + 接线
    src = rep(src, "copySelected:ht,pasteSelected:wt}=Nl(V,N,t,Y,q)", "copySelected:ht,pasteSelected:wt,pinSelected:ztPin}=Nl(V,N,t,Y,q)")
    src = rep(src, 'onPaste:G(wt),onClear:X},null,8,["selected-count","onCopy","onPaste"])',
              'onPaste:G(wt),onPin:G(ztPin),onClear:X},null,8,["selected-count","onCopy","onPaste","onPin"])')

    # 4) 右键菜单：emits + 悬浮中转菜单项 + 接线
    src = rep(src, 'canFavorite:{type:Boolean,default:!1}},emits:["favorite","delete"]',
              'canFavorite:{type:Boolean,default:!1}},emits:["favorite","pin","delete"]')
    pin_item = (
        'w("div",{class:"context-menu-item",onClick:s[5]||(s[5]=r=>n("pin"))},'
        '[w("svg",{viewBox:"0 0 24 24",fill:"none",xmlns:"http://www.w3.org/2000/svg"},'
        '[w("path",{d:"M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3v2h5.97v7l1 1 1-1v-7H18v-2c-1.66 0-3-1.34-3-3z",fill:"currentColor"})]),'
        'w("span",null,"悬浮中转",-1)]),'
    )
    src = rep(src, 'onClick:s[2]||(s[2]=ve(()=>{},["stop"]))},[e.canFavorite?',
              'onClick:s[2]||(s[2]=ve(()=>{},["stop"]))},[' + pin_item + 'e.canFavorite?')
    src = rep(src, 'onFavorite:_,onDelete:y},null,8,["show","x","y","can-favorite"])',
              'onFavorite:_,onPin:async()=>{const M=He.value.item;if(M)await ztPinItem(M)},onDelete:y},null,8,["show","x","y","can-favorite","onPin"])')

    # 5) onPluginEnter：处理 pindata / pinscreen 特征码
    src = rep(src, 'window.ztools.onPluginEnter(()=>{pt()}),',
              'window.ztools.onPluginEnter(E=>{if(E&&E.code==="pindata"){ztEnterPin(E);return}if(E&&E.code==="pinscreen"){ztOpenPinScreen();return}pt()}),')

    # 6) 模块级函数注入
    src = rep(src, "function Nl(", ZTPIN_FUNCS, expect=1)

    with open(bundle, "w", encoding="utf-8", newline="") as f:
        f.write(src)


def patch_plugin_json(root):
    pj = os.path.join(root, "plugin.json")
    d = json.load(open(pj, encoding="utf-8"))
    codes = [f.get("code") for f in d.get("features", [])]
    changed = False
    if "pinscreen" not in codes:
        d["features"].append({
            "code": "pinscreen",
            "explain": "剪贴板以小窗口模式悬浮屏幕上",
            "cmds": ["悬浮剪贴板", "悬浮剪切板"]
        })
        changed = True
    if "pindata" not in codes:
        d["features"].append({
            "code": "pindata",
            "explain": "内容加固定到悬浮屏幕的临时中转站",
            "cmds": [
                {"type": "over", "label": "文本悬浮中转"},
                {"type": "img", "label": "图像悬浮中转"},
                {"type": "files", "label": "文件悬浮中转"}
            ]
        })
        changed = True
    if changed:
        with open(pj, "w", encoding="utf-8", newline="") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("plugin.json 已添加 pindata / pinscreen 特征码")


def main():
    if not os.path.exists(ASAR):
        raise SystemExit(f"找不到 {ASAR}")

    # 补丁源：优先原始备份（保证可重复升级），否则当前未打补丁的 asar
    source = ASAR
    with open(ASAR, "rb") as f:
        content = f.read()
    if MARKER.encode() in content:
        if os.path.exists(BACKUP):
            source = BACKUP
            print("当前 asar 已有旧补丁，改用原始备份重打 v2 ...")
        elif os.path.exists(ORIG):
            source = ORIG
            print("当前 asar 已有旧补丁，改用原始副本重打 v2 ...")
        else:
            raise SystemExit("已打补丁但找不到原始备份，无法安全重打。")

    work = tempfile.mkdtemp(prefix="clipboard-pin-")
    try:
        node = shutil.which("node") or r"D:\Software_Data\nodejs\node.exe"
        reqjs = os.path.join(ASSETS, "_asar_req.js")

        print("解包剪贴板插件（源:", os.path.basename(source), "）...")
        subprocess.run([node, reqjs, "extract", source, work], check=True, capture_output=True, text=True)
        bundle = find_bundle(work)
        if not bundle:
            raise SystemExit("未找到插件主 bundle")
        patch_bundle(bundle)

        r = subprocess.run([node, "--check", bundle], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("bundle 语法检查失败：" + r.stderr[:400])
        print("bundle 语法检查通过")

        patch_plugin_json(work)
        shutil.copyfile(os.path.join(ASSETS, "pin.html"), os.path.join(work, "pin.html"))
        shutil.copyfile(os.path.join(ASSETS, "pin-preload.js"), os.path.join(work, "pin-preload.js"))

        css = os.path.join(work, "assets", "index-CgQaXsPA.css")
        if os.path.exists(css):
            css_src = open(css, encoding="utf-8").read()
            if ".sidebar-btn.pin-btn" not in css_src:
                css_src += "\n.sidebar-btn.pin-btn[data-v-23b151c6]:hover{color:#ffb74d;border-color:#ffb74d}\n"
                with open(css, "w", encoding="utf-8", newline="") as f:
                    f.write(css_src)

        if not os.path.exists(BACKUP):
            if os.path.exists(ORIG):
                shutil.copyfile(ORIG, BACKUP)
            else:
                shutil.copyfile(ASAR, BACKUP)
        print("重打包 ...")
        subprocess.run([node, reqjs, "pack", work, ASAR], check=True, capture_output=True, text=True)

        # 同步注册表特征码 + 清指令缓存（指令索引来自安装时的注册表快照）
        subprocess.run([node, os.path.join(ASSETS, "update-registry.js")], check=True, capture_output=True, text=True)
        print("完成。重启 ZTools 后生效：")
        print("  - 剪贴板侧边栏图钉按钮 / 右键菜单「悬浮中转」-> 中转站窗口（累积、持久化、可拖出）")
        print("  - 关键词「悬浮剪贴板」-> 悬浮历史窗口；选中文字/图片/文件 -> 文本/图像/文件悬浮中转")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
