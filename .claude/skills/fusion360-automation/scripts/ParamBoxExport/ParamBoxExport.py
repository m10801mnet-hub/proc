# Fusion スクリプト：パラメータ付きの箱（外形・肉厚）を作り、STL/STEP を書き出す雛形。
# 置き場所: %APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\ParamBoxExport\ParamBoxExport.py
# 実行: Fusion で Shift+S → スクリプト → ParamBoxExport → 実行
# 寸法は下の PARAMS を書き換えるだけ（mm）。出力先: ドキュメント\クロードコード\fusion\
import os, traceback
import adsk.core, adsk.fusion

PARAMS = {'W': 120, 'D': 80, 'H': 60, 'T': 3}   # mm: 幅・奥行・高さ・肉厚
OUT_DIR = os.path.join(os.path.expanduser('~'), 'Documents', 'クロードコード', 'fusion')


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get(); ui = app.userInterface
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designType = adsk.fusion.DesignTypes.ParametricDesignType
        up = des.userParameters
        for k, v in PARAMS.items():
            up.add(k, adsk.core.ValueInput.createByString(f'{v} mm'), 'mm', '')
        root = des.rootComponent
        sk = root.sketches.add(root.xYConstructionPlane)
        lines = sk.sketchCurves.sketchLines
        rect = lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(1, 1, 0))
        dims = sk.sketchDimensions
        dW = dims.addDistanceDimension(rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
                                       adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(0.5, -1, 0))
        dW.parameter.expression = 'W'
        dD = dims.addDistanceDimension(rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
                                       adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-1, 0.5, 0))
        dD.parameter.expression = 'D'
        ext = root.features.extrudeFeatures.addSimple(
            sk.profiles.item(0), adsk.core.ValueInput.createByString('H'),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        body = ext.bodies.item(0)
        # 上面を開口して肉厚 T の箱（シェル）
        top = max(body.faces, key=lambda f: f.centroid.z)
        faces = adsk.core.ObjectCollection.create(); faces.add(top)
        sh = root.features.shellFeatures.createInput(faces, False)
        sh.insideThickness = adsk.core.ValueInput.createByString('T')
        root.features.shellFeatures.add(sh)

        os.makedirs(OUT_DIR, exist_ok=True)
        name = 'box_{W}x{D}x{H}_t{T}'.format(**PARAMS)
        em = des.exportManager
        stl = em.createSTLExportOptions(root, os.path.join(OUT_DIR, name + '.stl'))
        stl.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(stl)
        em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, name + '.step'), root))
        ui.messageBox(f'exported to {OUT_DIR}\\{name}.stl / .step')
    except Exception:
        if ui:
            ui.messageBox('Failed:\n' + traceback.format_exc())
