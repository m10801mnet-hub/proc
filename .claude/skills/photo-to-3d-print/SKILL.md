---
name: photo-to-3d-print
description: 実物の写真（ネット上の商品写真・自分で撮った写真）から3Dモデルを作り、穴のない（watertight）STL/OBJに仕上げる。多視点写真→Tripo/Hunyuan等の画像→3D→メッシュ修復→向き・寸法合わせ→軽量版作成→配布用zipまで。「写真から立体」「フォトグラメトリ」「Tripo」「STLにして」「穴のない」「3Dプリント用データ」で発動。
---

# 写真 → 3Dプリント用メッシュ（検証済みパイプライン）

## 結論
多視点（正面・左・背面・右）の**同一個体の実物写真**を Image-to-3D に入れるのが最も忠実。AIで描いた三面図や自作CGより精度が出る。

## 手順
1. **写真集め**：同じフィギュア／造形物を別角度で撮った写真を最低3枚（正面・側面・背面）。通販の商品ページ（Shopify系は `https://<shop>/products/<handle>` のHTML内 `cdn/shop/products/...-0.jpg ...-3.jpg`）が狙い目。ピクセル数は大きいほど良い。
   - 例：タカラトミー「モンコレ MS-01 ピカチュウ」→ japan-figure.com の4枚（正面寄り・左側面・背面寄り・底面）で高精度に再現できた。
2. **前処理**：白背景・被写体中央。小さい画像はLanczosで1024pxに拡大（AI補完はしない）。
3. **立体化（Higgsfield MCP経由）**
   - `tripo_h3_1_multiview_to_3d`：2〜4枚、順序は 正面→左→背面→右。9クレジット。テクスチャ付きGLB。
   - `hunyuan3d_v3_image_to_3d`：単一/複数画像。Geometryのみ7クレジット。
   - 必ず `get_cost:true` で事前見積もり。無料プランは画像生成（gpt_image）不可。
   - アップロード：`media_upload` → 返ってきた URL に `curl -X PUT -H "Content-Type: image/jpeg" -H "If-None-Match: *" --data-binary @file` → `media_confirm`。
4. **修復と仕上げ（trimesh）**
```python
m = trimesh.load('model.glb', force='mesh')
vc = m.visual.to_color().vertex_colors
g = trimesh.Trimesh(m.vertices, m.faces, vertex_colors=vc, process=False)
g.merge_vertices(merge_tex=True, merge_norm=True)   # ← UV継ぎ目で割れた頂点を結合。これだけでwatertightになることが多い
# GLB(Y-up, 顔+X) → Z-up, 正面−Y, 底面Z=0, 高さ100mm
R = [[0,0,-1],[-1,0,0],[0,1,0]]
```
   - 検査は必ず数値で：`is_watertight`, `is_winding_consistent`, `is_volume`, `euler_number==2`, 境界エッジ0, 非多様体エッジ0, `body_count==1`。
   - **pymeshfix は最初に使わない**（watertightなメッシュを壊した実例あり）。間引き後に非多様体が出たときだけ使う。
   - 軽量版：`fast_simplification.simplify(..., target_reduction=0.75)` → 非多様体を pymeshfix で修復 → 元メッシュから最近傍で頂点色を転写。
   - 向き確認は色で：背中の縞（茶色）の平均Yが＋なら正面は−Y。
5. **出力**：`*_100mm.stl`（単色）、`*_100mm.obj`（頂点カラー付き）、`*_light.stl/obj`（約36万面）。zip化して配布。

## 環境の落とし穴
- Claude Code クラウドコンテナは CDN（cloudfront）・各種サイトに出られない。外部取得と重い処理は Higgsfield `sandbox_exec`（ネット可）で行う。
- sandbox_exec の pip は `PYTHONPATH=/pkg/:/root/` で権限エラー → `unset PYTHONPATH; export HOME=/home/user; python3 -m venv venv` で解決。
- sandbox → ユーザーへの受け渡しは `media_upload`（type=file）で恒久URLを発行。
- WebFetch は環境によりDNS失敗。検索は WebSearch、取得は sandbox の curl。

## 権利
キャラクター（ピカチュウ等）は著作物。個人利用の範囲に留め、販売・配布・ポートフォリオ公開は避けると明記して渡す。

## 品質の目安
プリント可否：検査全合格なら約90%。見た目の類似：多視点実写で約80%。元写真が500px程度だと細部（指の隙間など）は甘くなる。
