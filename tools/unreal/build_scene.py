"""
build_scene.py — STAGE 2 of the protocell UE 5.8 pipeline (reference look).

Builds the dividing-cell hero scene to match the reference footage:
  * M_Protocell — translucent bioluminescent MEMBRANE material:
        - cyan Fresnel rim (electric edge glow)
        - deep-blue subsurface interior
        - granular / fibrous interior from world-space 3D noise
        - depth-faded translucency so you see THROUGH the membrane
  * the cleavage mesh-sequence actors (all frames spawned, hidden; the Level
    Sequence reveals one per frame) + an occasional magenta-rim accent cell
  * a few drifting background cells (dark-field companions)
  * dark volumetric lighting + the vertical scan-sweep sheet
  * M_MicroscopeMask post-process: circular objective vignette (+ scan tint)
  * a graded PostProcessVolume (bloom, manual exposure, fringe)
  * the close-up CineCamera framing the hero cleavage

Run after import_mesh_sequence.py.

============================ VERSION-SENSITIVE ============================
FLAG-M : Material expression class names + connect_material_property enums
         (MP_EMISSIVE_COLOR, MP_OPACITY, MP_SUBSURFACE_COLOR,
         MP_WORLD_POSITION_OFFSET). Stable across 5.x; verify on 5.8 if
         Substrate is on — Substrate renames a few slots.
FLAG-T : Translucency wants TLM_SURFACE_PER_PIXEL_LIGHTING for the lit rim;
         for true volumetric interior use a Subsurface/Subsurface Profile
         shading model on a translucent or the new Substrate slab.
FLAG-PP: M_MicroscopeMask is a post-process material (domain = PostProcess).
         set_editor_property("material_domain", MD_POST_PROCESS) + adding it to
         PostProcessVolume.blendables is the version-sensitive pair.
==========================================================================
"""

import os
import sys
import math
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pcfg  # noqa: E402

import unreal  # noqa: E402

MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary


def _e(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


# --------------------------------------------------------------------------
def build_membrane_material():
    """M_Protocell — translucent cyan membrane with granular interior. FLAG-M/T."""
    mat = TOOLS.create_asset(pcfg.MAT_PROTOCELL, pcfg.MAT_PATH,
                             unreal.Material, unreal.MaterialFactoryNew())

    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)  # FLAG-T
    mat.set_editor_property("two_sided", True)
    try:
        mat.set_editor_property(
            "translucency_lighting_mode",
            unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)     # FLAG-T
    except Exception as ex:  # noqa: BLE001
        unreal.log_warning("[scene] TLM set failed: %s" % ex)

    # ---- granular interior: world-space 3D noise -> fibrous texture ---------
    noise = _e(mat, unreal.MaterialExpressionNoise, -900, 120)                  # FLAG-M
    try:
        noise.set_editor_property("scale", 0.06)
        noise.set_editor_property("levels", 5)
        noise.set_editor_property("output_min", 0.0)
        noise.set_editor_property("output_max", 1.0)
        noise.set_editor_property("function",
                                  unreal.NoiseFunction.NOISEFUNCTION_VORONOI)
    except Exception:  # noqa: BLE001
        pass
    wpos = _e(mat, unreal.MaterialExpressionWorldPosition, -1100, 120)
    MEL.connect_material_expressions(wpos, "", noise, "Position")

    # ---- Fresnel cyan rim ---------------------------------------------------
    fres = _e(mat, unreal.MaterialExpressionFresnel, -700, -160)
    fres.set_editor_property("exponent", 3.2)
    fres.set_editor_property("base_reflect_fraction", 0.04)

    rim_col = _e(mat, unreal.MaterialExpressionVectorParameter, -900, -260)
    rim_col.set_editor_property("parameter_name", "RimColor")
    rim_col.set_editor_property("default_value",
                                unreal.LinearColor(*pcfg.RIM_COLOR, 1.0))
    rim_gain = _e(mat, unreal.MaterialExpressionScalarParameter, -900, -120)
    rim_gain.set_editor_property("parameter_name", "RimGain")
    rim_gain.set_editor_property("default_value", 7.0)

    rim_a = _e(mat, unreal.MaterialExpressionMultiply, -500, -200)
    MEL.connect_material_expressions(rim_col, "", rim_a, "A")
    MEL.connect_material_expressions(fres, "", rim_a, "B")
    rim = _e(mat, unreal.MaterialExpressionMultiply, -320, -200)
    MEL.connect_material_expressions(rim_a, "", rim, "A")
    MEL.connect_material_expressions(rim_gain, "", rim, "B")

    # ---- interior glow = core color * noise (fibrous) ----------------------
    core_col = _e(mat, unreal.MaterialExpressionVectorParameter, -900, 0)
    core_col.set_editor_property("parameter_name", "CoreColor")
    core_col.set_editor_property("default_value",
                                 unreal.LinearColor(*pcfg.CORE_COLOR, 1.0))
    core_gain = _e(mat, unreal.MaterialExpressionScalarParameter, -700, 60)
    core_gain.set_editor_property("parameter_name", "CoreGain")
    core_gain.set_editor_property("default_value", 1.4)

    core_a = _e(mat, unreal.MaterialExpressionMultiply, -500, 40)
    MEL.connect_material_expressions(core_col, "", core_a, "A")
    MEL.connect_material_expressions(noise, "", core_a, "B")
    core = _e(mat, unreal.MaterialExpressionMultiply, -320, 40)
    MEL.connect_material_expressions(core_a, "", core, "A")
    MEL.connect_material_expressions(core_gain, "", core, "B")

    emissive = _e(mat, unreal.MaterialExpressionAdd, -120, -80)
    MEL.connect_material_expressions(rim, "", emissive, "A")
    MEL.connect_material_expressions(core, "", emissive, "B")
    MEL.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)  # FLAG-M

    # ---- opacity: rim-strong, body translucent, noise-broken ---------------
    op_floor = _e(mat, unreal.MaterialExpressionScalarParameter, -500, 260)
    op_floor.set_editor_property("parameter_name", "OpacityFloor")
    op_floor.set_editor_property("default_value", 0.10)
    noise_op = _e(mat, unreal.MaterialExpressionMultiply, -500, 360)
    op_noise_amt = _e(mat, unreal.MaterialExpressionScalarParameter, -700, 400)
    op_noise_amt.set_editor_property("parameter_name", "GranuleOpacity")
    op_noise_amt.set_editor_property("default_value", 0.22)
    MEL.connect_material_expressions(noise, "", noise_op, "A")
    MEL.connect_material_expressions(op_noise_amt, "", noise_op, "B")

    op_a = _e(mat, unreal.MaterialExpressionAdd, -300, 300)
    MEL.connect_material_expressions(fres, "", op_a, "A")
    MEL.connect_material_expressions(op_floor, "", op_a, "B")
    op_b = _e(mat, unreal.MaterialExpressionAdd, -160, 320)
    MEL.connect_material_expressions(op_a, "", op_b, "A")
    MEL.connect_material_expressions(noise_op, "", op_b, "B")
    op = _e(mat, unreal.MaterialExpressionClamp, 0, 320)
    MEL.connect_material_expressions(op_b, "", op, "")
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)   # FLAG-M

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)

    mi = TOOLS.create_asset(pcfg.MAT_INST, pcfg.MAT_PATH,
                            unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, mat)
    EAL.save_loaded_asset(mi)

    # magenta accent variant (the occasional pink-rimmed cell in the reference)
    mi_acc = TOOLS.create_asset(pcfg.MAT_INST + "_Accent", pcfg.MAT_PATH,
                                unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi_acc, mat)
    MEL.set_material_instance_vector_parameter_value(
        mi_acc, "RimColor", unreal.LinearColor(*pcfg.ACCENT_COLOR, 1.0))
    EAL.save_loaded_asset(mi_acc)
    unreal.log("[scene] built %s (+ instance, + accent)" % pcfg.MAT_PROTOCELL)
    return mi, mi_acc


# --------------------------------------------------------------------------
def build_microscope_mask():
    """M_MicroscopeMask — post-process circular objective vignette. FLAG-PP."""
    if not pcfg.USE_MICROSCOPE_MASK:
        return None
    mat = TOOLS.create_asset(pcfg.MAT_MASK, pcfg.MAT_PATH,
                             unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)  # FLAG-PP

    # radial distance from screen centre -> dark outside a circle
    uv = _e(mat, unreal.MaterialExpressionTextureCoordinate, -800, 0)
    ctr = _e(mat, unreal.MaterialExpressionConstant2Vector, -800, 140)
    ctr.set_editor_property("r", 0.5)
    ctr.set_editor_property("g", 0.5)
    sub = _e(mat, unreal.MaterialExpressionSubtract, -600, 60)
    MEL.connect_material_expressions(uv, "", sub, "A")
    MEL.connect_material_expressions(ctr, "", sub, "B")
    dist = _e(mat, unreal.MaterialExpressionLength, -440, 60)  # FLAG-M (Length node)
    MEL.connect_material_expressions(sub, "", dist, "")
    # smoothstep-ish mask via 1 - saturate((d - r)/feather)
    radius = _e(mat, unreal.MaterialExpressionScalarParameter, -600, 200)
    radius.set_editor_property("parameter_name", "MaskRadius")
    radius.set_editor_property("default_value", 0.46)
    dminus = _e(mat, unreal.MaterialExpressionSubtract, -280, 90)
    MEL.connect_material_expressions(dist, "", dminus, "A")
    MEL.connect_material_expressions(radius, "", dminus, "B")
    feather = _e(mat, unreal.MaterialExpressionScalarParameter, -280, 200)
    feather.set_editor_property("parameter_name", "Feather")
    feather.set_editor_property("default_value", 0.06)
    dn = _e(mat, unreal.MaterialExpressionDivide, -120, 110)
    MEL.connect_material_expressions(dminus, "", dn, "A")
    MEL.connect_material_expressions(feather, "", dn, "B")
    sat = _e(mat, unreal.MaterialExpressionSaturate, 40, 110)
    MEL.connect_material_expressions(dn, "", sat, "")
    one_minus = _e(mat, unreal.MaterialExpressionOneMinus, 200, 110)
    MEL.connect_material_expressions(sat, "", one_minus, "")

    scene = _e(mat, unreal.MaterialExpressionSceneTexture, 40, -120)
    try:
        scene.set_editor_property("scene_texture_id",
                                  unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)  # FLAG-PP
    except Exception:  # noqa: BLE001
        pass
    masked = _e(mat, unreal.MaterialExpressionMultiply, 360, 0)
    MEL.connect_material_expressions(scene, "Color", masked, "A")
    MEL.connect_material_expressions(one_minus, "", masked, "B")
    MEL.connect_material_property(masked, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    unreal.log("[scene] built %s (post-process objective mask)" % pcfg.MAT_MASK)
    return mat


# --------------------------------------------------------------------------
def _spawn(cls, loc, rot=None):
    return unreal.EditorLevelLibrary.spawn_actor_from_class(
        cls, loc, rot or unreal.Rotator(0, 0, 0))


def build_scene(mi, mi_acc, mask_mat):
    pcfg.banner("STAGE 2 — hero cleavage scene (reference look)")

    # ---- the cleavage mesh frames: spawn all, hide all but frame 0 ---------
    # make_sequence.py keys each actor's visibility so exactly one shows / frame.
    frame_actors = []
    i = 0
    while True:
        name = "%s/%s%04d" % (pcfg.MESH_PATH, pcfg.MESH_SEQ_PREFIX, i)
        if not EAL.does_asset_exist(name):
            break
        sm = EAL.load_asset(name)
        a = _spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
        comp = a.static_mesh_component
        comp.set_static_mesh(sm)
        comp.set_material(0, mi)
        a.set_actor_hidden_in_game(i != 0)
        a.set_actor_label("Cleave_%04d" % i)
        frame_actors.append(a)
        i += 1
    unreal.log("[scene] spawned %d cleavage frame actors" % len(frame_actors))

    # ---- drifting background cells (dark-field companions) -----------------
    random.seed(7)
    base = EAL.load_asset("%s/%s0000" % (pcfg.MESH_PATH, pcfg.MESH_SEQ_PREFIX))
    for n in range(pcfg.BG_CELL_COUNT):
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(160, 320)
        loc = unreal.Vector(math.cos(ang) * rad,
                            random.uniform(120, 320),         # behind hero
                            math.sin(ang) * rad)
        a = _spawn(unreal.StaticMeshActor, loc,
                   unreal.Rotator(random.uniform(0, 360),
                                  random.uniform(0, 360),
                                  random.uniform(0, 360)))
        s = random.uniform(0.25, 0.6)
        a.set_actor_scale3d(unreal.Vector(s, s, s))
        comp = a.static_mesh_component
        if base:
            comp.set_static_mesh(base)
        comp.set_material(0, mi_acc if n % 4 == 0 else mi)  # ~1 in 4 magenta
        a.set_actor_label("BgCell_%02d" % n)

    # ---- dark world + volumetric fog ---------------------------------------
    fog = _spawn(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
    fc = fog.get_component()
    fc.set_editor_property("fog_density", 0.07)
    fc.set_editor_property("volumetric_fog", True)
    fc.set_editor_property("fog_inscattering_color",
                           unreal.LinearColor(0.004, 0.02, 0.05, 1.0))

    # cool rim key + cooler back rim so the membrane edge reads cyan
    key = _spawn(unreal.SpotLight, unreal.Vector(-160, -120, 120),
                 unreal.Rotator(-22, 35, 0))
    kc = key.spot_light_component
    kc.set_editor_property("intensity", 11000.0)
    kc.set_editor_property("light_color", unreal.Color(120, 210, 255))
    kc.set_editor_property("attenuation_radius", 1400.0)
    kc.set_editor_property("volumetric_scattering_intensity", 3.0)

    back = _spawn(unreal.SpotLight, unreal.Vector(120, 220, -60),
                  unreal.Rotator(15, -150, 0))
    bc = back.spot_light_component
    bc.set_editor_property("intensity", 7000.0)
    bc.set_editor_property("light_color", unreal.Color(80, 170, 255))
    bc.set_editor_property("volumetric_scattering_intensity", 2.0)

    # ---- vertical scan-sweep sheet (make_sequence.py slides it) -------------
    scan = _spawn(unreal.RectLight, unreal.Vector(-180, -40, 0),
                  unreal.Rotator(0, 0, 90))
    sc = scan.rect_light_component
    sc.set_editor_property("intensity", 26000.0)
    sc.set_editor_property("light_color", unreal.Color(190, 245, 255))
    sc.set_editor_property("source_width", 4.0)
    sc.set_editor_property("source_height", 520.0)
    sc.set_editor_property("attenuation_radius", 700.0)
    sc.set_editor_property("volumetric_scattering_intensity", 7.0)
    scan.set_actor_label("ScanSweep")

    # ---- graded PostProcessVolume (+ microscope mask blendable) ------------
    ppv = _spawn(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_editor_property("unbound", True)
    s = ppv.settings
    s.set_editor_property("override_bloom_intensity", True)
    s.set_editor_property("bloom_intensity", 2.0)
    s.set_editor_property("override_auto_exposure_method", True)
    s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_bias", True)
    s.set_editor_property("auto_exposure_bias", 11.0)
    s.set_editor_property("override_scene_fringe_intensity", True)
    s.set_editor_property("scene_fringe_intensity", 2.5)   # microscope chromatic edge
    if mask_mat is not None:
        try:
            arr = unreal.Array(unreal.WeightedBlendable)
            wb = unreal.WeightedBlendable()
            wb.set_editor_property("weight", 1.0)
            wb.set_editor_property("object", mask_mat)
            arr.append(wb)
            s.set_editor_property("weighted_blendables",
                                  unreal.WeightedBlendables(array=arr))          # FLAG-PP
        except Exception as ex:  # noqa: BLE001
            unreal.log_warning("[scene] mask blendable attach failed (%s); add "
                               "M_MicroscopeMask to the PPV manually" % ex)
    ppv.set_editor_property("settings", s)

    # ---- close-up CineCamera on the hero cleavage --------------------------
    cam = _spawn(unreal.CineCameraActor, unreal.Vector(0, -210, 30),
                 unreal.Rotator(-6, 90, 0))
    cam.set_actor_label("HeroCamera")
    ccc = cam.get_cine_camera_component()
    try:
        ccc.set_editor_property("current_focal_length", 50.0)
    except Exception:  # noqa: BLE001
        pass
    unreal.log("[scene] DONE — %d frames, %d bg cells, mask=%s"
               % (len(frame_actors), pcfg.BG_CELL_COUNT, mask_mat is not None))
    return frame_actors


# --------------------------------------------------------------------------
def main():
    mi, mi_acc = build_membrane_material()
    mask_mat = build_microscope_mask()
    build_scene(mi, mi_acc, mask_mat)
    if not EAL.does_directory_exist(pcfg.LEVEL_PATH):
        EAL.make_directory(pcfg.LEVEL_PATH)
    try:
        unreal.EditorLevelLibrary.save_current_level()
    except Exception as ex:  # noqa: BLE001
        unreal.log_warning("[scene] save_current_level failed (%s); save manually" % ex)
    unreal.log("[scene] level saved")


if __name__ == "__main__":
    main()
