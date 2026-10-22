---
name: unreal-engine-automation
description: Unreal Engine 5 をPythonとコマンドラインで自動化する。空間・展示・テーマパーク計画のビジュアライズ、Rhino/Blender/写真3DモデルのFBX/GLB/Datasmith取り込み、マテリアル割当、カメラ配置、高解像度スクリーンショット・Movie Render Queue書き出し。「アンリアル」「Unreal」「UE5」「ウォークスルー」「空間パース」で発動。
---

# Unreal Engine 5 自動化

## 準備（一度だけ）
- Edit → Plugins で **Python Editor Script Plugin**, **Editor Scripting Utilities**, **Datasmith Importer**, **Movie Render Queue** を有効化 → 再起動。
- Project Settings → Python → Startup Scripts に初期化スクリプトを登録可。

## 実行方法（PC上）
- エディタ内：Output Log の入力欄を `Python` にして `py "C:/path/job.py"`
- ヘッドレス：`UnrealEditor-Cmd.exe "C:/Proj/Proj.uproject" -run=pythonscript -script="C:/path/job.py" -unattended -nosplash`

## 台本：`scripts/import_and_shoot.py`（構文チェック済み・PCで要検証）
モデル（GLB/FBX/OBJ）を `/Game/Imports` に取り込み → 原点に配置 → 目線1,600mm・距離6mの4方向カメラを置いて 4K 静止画を4枚。
`UnrealEditor-Cmd.exe "C:/Proj/Proj.uproject" -ExecutePythonScript="C:/path/import_and_shoot.py C:/in/model.glb"`
出力：`<Project>/Saved/Screenshots/`

## よく使うコード
```python
import unreal
# 取り込み（FBX/GLB/OBJ）
task = unreal.AssetImportTask(); task.filename = r"C:/in/model.glb"; task.destination_path = "/Game/Imports"
task.automated = True; task.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
# 配置
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mesh = unreal.load_asset("/Game/Imports/model")
actor = eas.spawn_actor_from_object(mesh, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
# スクリーンショット
unreal.AutomationLibrary.take_high_res_screenshot(3840, 2160, "shot01.png")
```
- 単位は **cm**。Rhino(mm)→FBX書き出し時に単位を確認（スケール0.1/10倍ずれが最頻トラブル）。
- Rhinoからは Datasmith（Rhino用エクスポーター）がレイヤー・マテリアルを保持して最も安定。

## 提案用ビジュアル標準
カメラ：目線高1,600mm、35mm換算24〜35mm。昼・夕・夜の3ライティング。4K静止画3枚＋20秒ウォークスルー（MRQ、1080p/30fps）。
