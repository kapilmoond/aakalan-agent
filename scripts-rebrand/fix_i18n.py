#!/usr/bin/env python3
import pathlib

for lang in ("ar", "ja", "zh", "zh-hant"):
    p = pathlib.Path(r"C:\Users\LAPTOP PC\Desktop\3_Apps_and_Development\aakalan agent\apps\desktop\src\i18n") / f"{lang}.ts"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    orig = t
    t = t.replace("リモートの hermes バイナリへのフルパス。空欄 = 自動検出。", "リモートのエージェントバイナリへのフルパス。空欄 = 自動検出。")
    t = t.replace("远程 hermes 可执行文件的完整路径。留空 = 自动检测。", "远程代理程序可执行文件的完整路径。留空 = 自动检测。")
    t = t.replace("遠端 hermes 執行檔的完整路徑。留空 = 自動偵測。", "遠端代理程式執行檔的完整路徑。留空 = 自動偵測。")
    if t != orig:
        p.write_text(t, encoding="utf-8")
        print(f"updated {lang}.ts")
print("done")
