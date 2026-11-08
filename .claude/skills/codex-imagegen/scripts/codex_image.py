#!/usr/bin/env python3
"""Claude Code から Codex CLI の画像生成（$imagegen / image_generation）を呼ぶラッパー。

使い方:
  python codex_image.py check
  python codex_image.py gen "京都の町家を改装した展示ブース、木とFRP、昼光" -o out/booth.png
  python codex_image.py gen "同じ構図で夜景に" -i out/booth.png -o out/booth_night.png
  python codex_image.py gen "プロンプト" -o out/var.png -n 3 --size 1536x1024

仕組み:
  1) codex exec を非対話で起動し、画像生成ツールで生成させる
  2) Codex が保存した $CODEX_HOME/generated_images/... のうち、起動後に増えた画像を拾う
  3) 指定の出力パスへコピーし、結果を JSON で標準出力に出す（Claude が読む用）
Windows / macOS / Linux 共通。標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def codex_bin() -> str:
    exe = os.environ.get("CODEX_BIN") or shutil.which("codex") or shutil.which("codex.cmd")
    if not exe:
        sys.exit(json.dumps({"ok": False, "error": "codex が見つからない。`npm i -g @openai/codex` でインストールし、`codex login` を実行する。"}, ensure_ascii=False))
    return exe


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))


def snapshot(root: Path) -> dict[Path, float]:
    if not root.exists():
        return {}
    return {p: p.stat().st_mtime for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXT}


def cmd_check(_: argparse.Namespace) -> int:
    exe = codex_bin()
    out = {"codex": exe}
    v = subprocess.run([exe, "--version"], capture_output=True, text=True)
    out["version"] = (v.stdout or v.stderr).strip()
    s = subprocess.run([exe, "login", "status"], capture_output=True, text=True)
    out["login"] = (s.stdout + s.stderr).strip()
    f = subprocess.run([exe, "features", "list"], capture_output=True, text=True)
    line = next((l for l in f.stdout.splitlines() if l.split()[:1] == ["image_generation"]), "")
    out["image_generation"] = " ".join(line.split()) or "不明（features list に無い）"
    out["ok"] = s.returncode == 0 and line.endswith("true")
    out["generated_images_dir"] = str(codex_home() / "generated_images")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 1


def build_prompt(a: argparse.Namespace, out_dir: Path) -> str:
    lines = [
        "Use your built-in image generation tool ($imagegen) to create the image described below.",
        "Do not draw it with code, SVG, HTML, canvas or Python. Do not edit any other files.",
        f"Generate exactly {a.n} image(s).",
    ]
    if a.size:
        lines.append(f"Size / aspect: {a.size}.")
    if a.quality:
        lines.append(f"Quality: {a.quality}.")
    if a.transparent:
        lines.append("Use a transparent background.")
    if a.image:
        lines.append("The attached image(s) are references: edit / follow them as the request says.")
    lines += [
        f"After generating, copy the result file(s) into this folder: {out_dir}",
        "Finally reply with only the absolute path(s) of the saved file(s), one per line.",
        "",
        "Request:",
        a.prompt,
    ]
    return "\n".join(lines)


def cmd_gen(a: argparse.Namespace) -> int:
    exe = codex_bin()
    if not os.environ.get("CODEX_SKIP_LOGIN_CHECK"):
        st = subprocess.run([exe, "login", "status"], capture_output=True, text=True)
        if st.returncode != 0:
            print(json.dumps({"ok": False, "error": "Codex 未ログイン。PCで `codex login`（ChatGPTアカウント）を一度実行する。",
                              "login": (st.stdout + st.stderr).strip()}, ensure_ascii=False))
            return 3
    out_path = Path(a.output).expanduser().resolve()
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_root = codex_home() / "generated_images"
    before = snapshot(gen_root)
    before_out = snapshot(out_dir)
    t0 = time.time()

    cmd = [exe, "exec", "--skip-git-repo-check", "--ephemeral", "--color", "never",
           "--sandbox", "workspace-write", "-C", str(out_dir),
           "--enable", "image_generation"]
    if a.model:
        cmd += ["-m", a.model]
    for img in a.image or []:
        cmd += ["-i", str(Path(img).expanduser().resolve())]
    cmd.append("-")  # プロンプトは stdin（日本語・改行・長文を安全に渡す）

    try:
        r = subprocess.run(cmd, input=build_prompt(a, out_dir), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "error": f"timeout {a.timeout}s"}, ensure_ascii=False))
        return 2

    # 新しく増えた画像：まず Codex 既定の保存先、次に出力フォルダ（Codex が直接置いた場合）
    new = [p for p, m in snapshot(gen_root).items() if p not in before or m > before[p]]
    if not new:
        new = [p for p, m in snapshot(out_dir).items()
               if (p not in before_out or m > before_out[p]) and m >= t0 - 1]
    new.sort(key=lambda p: p.stat().st_mtime)

    saved = []
    for i, src in enumerate(new):
        dst = out_path if len(new) == 1 else out_path.with_name(f"{out_path.stem}_{i + 1}{out_path.suffix}")
        if src.suffix.lower() != dst.suffix.lower():
            dst = dst.with_suffix(src.suffix.lower())
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        saved.append(str(dst))

    res = {"ok": bool(saved), "files": saved, "codex_exit": r.returncode,
           "seconds": round(time.time() - t0, 1)}
    if not saved:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-25:]
        res["error"] = "画像が生成されなかった。`python codex_image.py check` でログイン状態を確認。"
        res["codex_log_tail"] = tail
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if saved else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="codex のインストール・ログイン・画像生成機能を確認").set_defaults(fn=cmd_check)
    g = sub.add_parser("gen", help="画像を生成")
    g.add_argument("prompt")
    g.add_argument("-o", "--output", required=True, help="保存先 (例: out/booth.png)。複数枚なら _1, _2 を付ける")
    g.add_argument("-i", "--image", action="append", help="参照・編集元の画像（複数可）")
    g.add_argument("-n", type=int, default=1, help="枚数")
    g.add_argument("--size", help="例: 1024x1024 / 1536x1024 / 1024x1536 / 横長")
    g.add_argument("--quality", choices=["low", "medium", "high"])
    g.add_argument("--transparent", action="store_true", help="背景透過")
    g.add_argument("-m", "--model", help="Codex のエージェントモデル（通常は省略）")
    g.add_argument("--timeout", type=int, default=600)
    g.set_defaults(fn=cmd_gen)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
