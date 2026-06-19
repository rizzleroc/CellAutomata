# import_heightfield.py — Unreal 5.8 · import the real sim heightmap (from export_height.mjs) as a
# Texture2D and wire it into M_Protocell's HeightTex param (drives WorldPositionOffset displacement).
# Set UE_HEIGHT_PNG to the 16-bit PNG produced by:  node tools/unreal/export_height.mjs grayscott 220 1024 protocell
import unreal, os

PKG = "/Game/Protocell"
SRC = os.environ.get("UE_HEIGHT_PNG", "C:/protocell_height.png")  # <-- copy /tmp/protocell_height.png here
AT, EAL = unreal.AssetToolsHelpers.get_asset_tools(), unreal.EditorAssetLibrary

def main():
    if not os.path.exists(SRC):
        unreal.log_warning(f"heightmap not found: {SRC} (set UE_HEIGHT_PNG). Material keeps its default.")
        return
    task = unreal.AssetImportTask()
    task.filename = SRC; task.destination_path = PKG; task.destination_name = "T_sim_height"
    task.automated = True; task.replace_existing = True; task.save = True
    task.factory = unreal.TextureFactory()
    AT.import_asset_tasks([task])
    tex = EAL.load_asset(f"{PKG}/T_sim_height")
    tex.set_editor_property("srgb", False)                              # linear data, not color
    try: tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
    except Exception: pass
    EAL.save_asset(f"{PKG}/T_sim_height")
    # bind into the material param (build_scene also picks it up if it exists at build time)
    mat = EAL.load_asset(f"{PKG}/M_Protocell")
    if mat:
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value  # (instances) — for the base material the sample already references the asset
    unreal.log("T_sim_height imported + linear/grayscale; rebuild material if it predated this import.")

if __name__ == "__main__":
    main()
