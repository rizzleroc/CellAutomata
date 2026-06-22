"""
import_mesh_sequence.py — STAGE 1 (TRUE 3D path) of the protocell pipeline.

Imports the OBJ cleavage sequence produced by export_mesh.py as a set of
per-frame StaticMesh assets (SM_ProtoCleave_0000 ...). The Level Sequence
later shows exactly one of them per frame, so the cell genuinely cleaves on
screen — every frame is a real 3D Gray-Scott isosurface.

Run in-editor:   exec(open("import_mesh_sequence.py").read())
Or headless:     UnrealEditor-Cmd ... -ExecutePythonScript="import_mesh_sequence.py"

============================ VERSION-SENSITIVE ============================
FLAG-OBJ : UE 5.8 imports OBJ through INTERCHANGE. The AssetImportTask path
           below works for OBJ in 5.8, but if your project disabled the
           Interchange OBJ pipeline you must drive InterchangeManager directly.
FLAG-GC  : For a SINGLE animated asset instead of N static meshes, export an
           Alembic (.abc) from export_mesh.py's verts (or convert the OBJs with
           a DCC) and import as a GEOMETRY CACHE — then bind one Geometry Cache
           track in make_sequence.py instead of the per-frame swap. The
           per-frame StaticMesh swap below needs no extra plugins and is the
           most portable; Geometry Cache is smoother but needs the Alembic.
==========================================================================
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pcfg  # noqa: E402

import unreal  # noqa: E402

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary


def _ensure_dirs():
    for p in (pcfg.MESH_PATH, pcfg.MAT_PATH, pcfg.SEQ_PATH, pcfg.LEVEL_PATH):
        if not EAL.does_directory_exist(p):
            EAL.make_directory(p)


def _import_obj(obj_path, asset_name):
    """FLAG-OBJ: legacy task importer (Interchange-backed in 5.8)."""
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", obj_path)
    task.set_editor_property("destination_path", pcfg.MESH_PATH)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    TOOLS.import_asset_tasks([task])
    return EAL.load_asset("%s/%s" % (pcfg.MESH_PATH, asset_name))


def import_cleavage_sequence():
    pcfg.banner("STAGE 1 (3D) — import cleavage mesh sequence")
    _ensure_dirs()
    d = pcfg.MESH_SEQ_DIR
    if not os.path.isdir(d):
        unreal.log_warning("[mesh] no mesh dir: %s  (run export_mesh.py first)" % d)
        return []
    objs = sorted(f for f in os.listdir(d) if f.lower().endswith(".obj"))
    out = []
    for i, fn in enumerate(objs):
        name = "%s%04d" % (pcfg.MESH_SEQ_PREFIX, i)
        sm = _import_obj(os.path.join(d, fn), name)
        if sm:
            # Nanite is great for these dense translucent blobs; harmless if it
            # silently no-ops on a build that defaults it on.
            try:
                sm.set_editor_property("nanite_settings",
                                       unreal.MeshNaniteSettings(enabled=True))
            except Exception:  # noqa: BLE001
                pass
            EAL.save_loaded_asset(sm)
            out.append(sm)
        if i == 0 or i == len(objs) - 1 or i % 12 == 0:
            unreal.log("[mesh] imported %s" % name)
    unreal.log("[mesh] DONE — %d cleavage frames imported" % len(out))
    return out


if __name__ == "__main__":
    import_cleavage_sequence()
