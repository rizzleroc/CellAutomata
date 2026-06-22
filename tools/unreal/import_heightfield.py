"""
import_heightfield.py — STAGE 1 of the protocell UE 5.8 pipeline.

Imports the 16-bit displacement map(s) produced by export_height.mjs as
Texture2D assets, configured correctly for displacement (linear, no sRGB,
no lossy compression), and builds a finely subdivided plane mesh the
material will displace.

Run in-editor:   exec(open("import_heightfield.py").read())
Or headless:     UnrealEditor-Cmd ... -ExecutePythonScript="import_heightfield.py"

============================ VERSION-SENSITIVE ============================
UE 5.8 defaults to the INTERCHANGE import framework. The classic
AssetToolsHelpers.get_asset_tools().import_asset_tasks() path used below
still works for PNG in 5.8, but if your project has disabled the legacy
texture importer you must instead drive unreal.InterchangeManager. The
texture *settings* we apply afterwards are identical either way. The spot
is flagged FLAG-A below.

Building a subdivided plane from Python uses the MeshDescription API
(unreal.StaticMeshDescription). The exact builder calls moved around
between 5.2 and 5.5; if create_static_mesh_from_description errors on your
build, fall back to importing a subdivided plane FBX, or use the
"Displacement" Nanite workflow (FLAG-B) and skip the dense plane entirely.
==========================================================================
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pcfg  # noqa: E402

import unreal  # noqa: E402


# --------------------------------------------------------------------------
def _ensure_dirs():
    eal = unreal.EditorAssetLibrary
    for p in (pcfg.TEX_PATH, pcfg.MAT_PATH, pcfg.MESH_PATH,
              pcfg.SEQ_PATH, pcfg.LEVEL_PATH):
        if not eal.does_directory_exist(p):
            eal.make_directory(p)


def _configure_displacement_texture(tex):
    """Linear 16-bit heightmap: no sRGB, no lossy compression, no mips that
    would soften the domes. Applied identically regardless of importer."""
    tex.set_editor_property("srgb", False)
    # TC_Displacementmap keeps full precision and disables DXT block compression.
    tex.set_editor_property(
        "compression_settings",
        unreal.TextureCompressionSettings.TC_DISPLACEMENTMAP,
    )
    tex.set_editor_property("filter", unreal.TextureFilter.TF_BILINEAR)
    # Wrap so the toroidal Gray-Scott field tiles seamlessly.
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_WRAP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)


def _import_one(png_path, dest_path, asset_name):
    """FLAG-A: legacy task importer. Swap for InterchangeManager if your 5.8
    project has the legacy texture importer disabled."""
    if not os.path.isfile(png_path):
        unreal.log_warning("[import] missing PNG: %s" % png_path)
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", png_path)
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])

    full = "%s/%s" % (dest_path, asset_name)
    tex = unreal.EditorAssetLibrary.load_asset(full)
    if tex is None:
        unreal.log_warning("[import] failed to load imported asset: %s" % full)
        return None
    _configure_displacement_texture(tex)
    unreal.log("[import] imported + configured %s" % full)
    return tex


def import_hero_heightmap():
    return _import_one(pcfg.HEIGHT_PNG, pcfg.TEX_PATH, pcfg.TEX_HEIGHT)


def import_division_sequence():
    """Import every frame in seq/ as its own displacement texture so the
    Level Sequence can swap the material's height texture each frame
    (the spots literally divide). Returns the ordered list of textures."""
    d = pcfg.HEIGHT_SEQ_DIR
    if not os.path.isdir(d):
        unreal.log("[import] no sequence dir (%s) — single-frame hero only" % d)
        return []
    frames = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
    out = []
    for i, fn in enumerate(frames):
        name = "%s%04d" % (pcfg.TEX_SEQ_PREFIX, i)
        tex = _import_one(os.path.join(d, fn), pcfg.TEX_PATH, name)
        if tex:
            out.append(tex)
    unreal.log("[import] imported %d division frames" % len(out))
    return out


# --------------------------------------------------------------------------
def build_displacement_plane():
    """Create a flat, densely subdivided plane mesh centred at origin. The
    protocell material pushes its verts up along Z by the heightmap via WPO.

    FLAG-B: if you prefer Nanite displacement (5.3+), skip this dense plane,
    enable 'Nanite' + 'Displacement' on a simple plane, and plug the heightmap
    into the material's Displacement output instead of WPO. That path needs far
    fewer verts. This MeshDescription builder is the no-Nanite fallback."""
    sub = pcfg.PLANE_SUBDIV
    size = pcfg.PLANE_SIZE_CM
    half = size * 0.5

    mesh_desc = unreal.MeshDescription()  # FLAG-B: API name stable 5.2+, verify on 5.8
    builder = unreal.MeshDescriptionBuilder()
    builder.set_mesh_description(mesh_desc)
    builder.enable_poly_group_support()

    # vertices
    vids = []
    for j in range(sub + 1):
        for i in range(sub + 1):
            x = -half + size * (i / sub)
            y = -half + size * (j / sub)
            vids.append(builder.append_vertex(unreal.Vector(x, y, 0.0)))

    poly_group = builder.append_polygon_group()

    def vinst(i, j, u, v):
        inst = builder.append_vertex_instance(vids[j * (sub + 1) + i])
        builder.set_vertex_instance_normal(inst, unreal.Vector(0, 0, 1))
        builder.set_vertex_instance_uv(inst, unreal.Vector2D(u, v), 0)
        return inst

    for j in range(sub):
        for i in range(sub):
            u0, u1 = i / sub, (i + 1) / sub
            v0, v1 = j / sub, (j + 1) / sub
            a = vinst(i,     j,     u0, v0)
            b = vinst(i + 1, j,     u1, v0)
            c = vinst(i + 1, j + 1, u1, v1)
            d = vinst(i,     j + 1, u0, v1)
            builder.append_polygon(poly_group, [a, b, c, d])

    sm = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        pcfg.MESH_PLANE, pcfg.MESH_PATH, unreal.StaticMesh, None
    )
    # FLAG-B: build_static_mesh_from_descriptions exists 5.x; arg shape can vary.
    build_settings = unreal.MeshBuildSettings()
    build_settings.set_editor_property("use_full_precision_u_vs", True)
    sm.build_from_mesh_descriptions([mesh_desc])
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    unreal.log("[import] built %dx%d displacement plane (%d verts)"
               % (sub, sub, (sub + 1) ** 2))
    return sm


# --------------------------------------------------------------------------
def main():
    pcfg.banner("STAGE 1 — import heightfield + build plane")
    _ensure_dirs()
    hero = import_hero_heightmap()
    seq = import_division_sequence()
    plane = build_displacement_plane()
    unreal.log("[import] DONE  hero=%s seqFrames=%d plane=%s"
               % (bool(hero), len(seq), bool(plane)))


if __name__ == "__main__":
    main()
