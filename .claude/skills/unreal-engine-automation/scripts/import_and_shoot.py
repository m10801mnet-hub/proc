"""UE5: モデルを取り込み → 原点に配置 → 4方向のカメラから4K静止画。
エディタ内:  Output Log を Python にして  py "C:/path/import_and_shoot.py" "C:/in/model.glb"
ヘッドレス:  UnrealEditor-Cmd.exe "C:/Proj/Proj.uproject" -ExecutePythonScript="C:/path/import_and_shoot.py C:/in/model.glb"
必要プラグイン: Python Editor Script Plugin, Editor Scripting Utilities
"""
import math
import sys
import unreal

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:/in/model.glb"
DEST = "/Game/Imports"
DIST_CM = 600.0      # 被写体からカメラまでの距離（cm）
EYE_CM = 160.0       # 目線高さ 1,600mm

task = unreal.AssetImportTask()
task.filename = SRC
task.destination_path = DEST
task.automated = True
task.save = True
task.replace_existing = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.imported_object_paths)
unreal.log(f"imported: {paths}")

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
meshes = [unreal.load_asset(p) for p in paths]
meshes = [m for m in meshes if isinstance(m, unreal.StaticMesh)]
if not meshes:
    raise SystemExit("no static mesh imported")
actor = eas.spawn_actor_from_object(meshes[0], unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
origin, extent = actor.get_actor_bounds(False)
target = unreal.Vector(origin.x, origin.y, origin.z)

for i, (name, yaw) in enumerate((("front", 90), ("right", 180), ("back", 270), ("left", 0))):
    rad = math.radians(yaw)
    loc = unreal.Vector(target.x - DIST_CM * math.cos(rad), target.y - DIST_CM * math.sin(rad), EYE_CM)
    rot = unreal.MathLibrary.find_look_at_rotation(loc, target)
    cam = eas.spawn_actor_from_class(unreal.CameraActor, loc, rot)
    cam.set_actor_label(f"CAM_{name}")
    unreal.AutomationLibrary.take_high_res_screenshot(3840, 2160, f"shot_{i+1:02d}_{name}.png", camera=cam)
unreal.log("screenshots -> <Project>/Saved/Screenshots/")
