# build_scene.py — Unreal Engine 5.8 · "THIS ISN'T A CELL" hero proof-of-concept (scene + material + look).
# Run inside UE (Tools > Execute Python Script) or headless (see run_ue.sh).
# Builds: a bioluminescent translucent protocell material (emissive Fresnel rim + sim heightmap displacement),
# a dividing-cell rig (parent + 2 daughters + satellite colony), volumetric dark lighting, a scan-light,
# a graded PostProcessVolume, and a CineCamera. Sequencing + render are separate scripts.
#
# NOTE (honesty): authored against the stable UE5 `unreal` Python API; it was NOT run in-engine from this
# environment. Expect a TD to fix a few version-sensitive names (esp. material node enums under 5.8 and
# Movie Render Graph vs Movie Render Queue in render.py). Material/Niagara detail also in MATERIAL_SPEC.md.
import unreal

PKG = "/Game/Protocell"
MAP = f"{PKG}/Map_Protocell"
MAT = f"{PKG}/M_Protocell"
HEIGHT_TEX = f"{PKG}/T_sim_height"   # imported by import_heightfield.py (real grayscott data)

AT  = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

def _mk_expr(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)

def build_material():
    if EAL.does_asset_exist(MAT):
        EAL.delete_asset(MAT)
    mat = AT.create_asset("M_Protocell", PKG, unreal.Material, unreal.MaterialFactoryNew())
    # translucent, lit, two-sided glassy membrane
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
    mat.set_editor_property("two_sided", True)
    try: mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    except Exception: pass

    # --- animatable parameters (driven by Sequencer in make_sequence.py) ---
    p_emis = _mk_expr(mat, unreal.MaterialExpressionScalarParameter, -900, -200); p_emis.set_editor_property("parameter_name","EmissiveBoost"); p_emis.set_editor_property("default_value",6.0)
    p_scan = _mk_expr(mat, unreal.MaterialExpressionScalarParameter, -900,  -60); p_scan.set_editor_property("parameter_name","ScanPhase");     p_scan.set_editor_property("default_value",0.0)
    p_disp = _mk_expr(mat, unreal.MaterialExpressionScalarParameter, -900,  500); p_disp.set_editor_property("parameter_name","DisplaceScale"); p_disp.set_editor_property("default_value",18.0)
    c_cyan = _mk_expr(mat, unreal.MaterialExpressionVectorParameter, -900, -340); c_cyan.set_editor_property("parameter_name","RimColor");      c_cyan.set_editor_property("default_value", unreal.LinearColor(0.0,0.85,1.0,1.0))
    c_core = _mk_expr(mat, unreal.MaterialExpressionVectorParameter, -900, -460); c_core.set_editor_property("parameter_name","CoreColor");     c_core.set_editor_property("default_value", unreal.LinearColor(0.9,0.1,0.7,1.0))

    # --- EMISSIVE = (Fresnel rim * RimColor + CoreColor*0.15 + ScanBand) * EmissiveBoost ---
    fres = _mk_expr(mat, unreal.MaterialExpressionFresnel, -640, -340); fres.set_editor_property("exponent", 3.2); fres.set_editor_property("base_reflect_fraction", 0.04)
    rim  = _mk_expr(mat, unreal.MaterialExpressionMultiply, -440, -360); MEL.connect_material_expressions(fres,"",rim,"A"); MEL.connect_material_expressions(c_cyan,"",rim,"B")
    addc = _mk_expr(mat, unreal.MaterialExpressionAdd, -300, -360); MEL.connect_material_expressions(rim,"",addc,"A"); MEL.connect_material_expressions(c_core,"",addc,"B")
    emul = _mk_expr(mat, unreal.MaterialExpressionMultiply, -160, -300); MEL.connect_material_expressions(addc,"",emul,"A"); MEL.connect_material_expressions(p_emis,"",emul,"B")
    MEL.connect_material_property(emul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # --- OPACITY = Fresnel rim (glassy: rim opaque, core clear) ---
    op = _mk_expr(mat, unreal.MaterialExpressionMultiply, -300, 120); MEL.connect_material_expressions(fres,"",op,"A")
    opk= _mk_expr(mat, unreal.MaterialExpressionConstant, -440, 180); opk.set_editor_property("r", 0.9); MEL.connect_material_expressions(opk,"",op,"B")
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)

    base = _mk_expr(mat, unreal.MaterialExpressionConstant3Vector, -300, 280); base.set_editor_property("constant", unreal.LinearColor(0.02,0.06,0.10,1.0)); MEL.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR)
    rough= _mk_expr(mat, unreal.MaterialExpressionConstant, -300, 360); rough.set_editor_property("r",0.18); MEL.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS)

    # --- WORLD POSITION OFFSET = VertexNormalWS * (heightTex.r * DisplaceScale) : real sim displacement ---
    tex = _mk_expr(mat, unreal.MaterialExpressionTextureSampleParameter2D, -640, 520); tex.set_editor_property("parameter_name","HeightTex")
    if EAL.does_asset_exist(HEIGHT_TEX):
        tex.set_editor_property("texture", EAL.load_asset(HEIGHT_TEX))
    hd = _mk_expr(mat, unreal.MaterialExpressionMultiply, -420, 540); MEL.connect_material_expressions(tex,"R",hd,"A"); MEL.connect_material_expressions(p_disp,"",hd,"B")
    nrm= _mk_expr(mat, unreal.MaterialExpressionVertexNormalWS, -420, 640)
    wpo= _mk_expr(mat, unreal.MaterialExpressionMultiply, -200, 580); MEL.connect_material_expressions(nrm,"",wpo,"A"); MEL.connect_material_expressions(hd,"",wpo,"B")
    MEL.connect_material_property(wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    MEL.recompile_material(mat); EAL.save_asset(MAT)
    unreal.log("M_Protocell built")
    return mat

def spawn_cell(eas, mat, label, loc, scale):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(0,0,0))
    a.set_actor_label(label); a.set_actor_scale3d(unreal.Vector(scale,scale,scale))
    smc = a.static_mesh_component
    smc.set_static_mesh(EAL.load_asset("/Engine/BasicShapes/Sphere.Sphere"))
    smc.set_material(0, mat)
    a.set_folder_path("Protocell")
    return a

def build_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.new_level(MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mat = build_material()

    # dividing-cell rig (Sequencer animates these — see make_sequence.py)
    spawn_cell(eas, mat, "ParentCell",  (0,0,0),     1.6)
    spawn_cell(eas, mat, "DaughterA",   (-60,0,0),   0.02)
    spawn_cell(eas, mat, "DaughterB",   ( 60,0,0),   0.02)
    import math
    for i in range(9):  # satellite colony so the frame never reads sparse
        an = (i/9)*2*math.pi; r = 220+ (i%3)*40
        spawn_cell(eas, mat, f"Sat_{i}", (math.cos(an)*r, math.sin(an)*r, (i%2)*30-15), 0.5+0.25*(i%3))

    # --- lighting: dark volumetric bioluminescent chamber ---
    key = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,400), unreal.Rotator(-55,40,0))
    key.light_component.set_intensity(1.2); key.light_component.set_light_color(unreal.LinearColor(0.5,0.7,1.0))
    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0,0,300)); sky.light_component.set_intensity(0.25)
    rcy = eas.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-300,0,120), unreal.Rotator(0,0,0)); rcy.light_component.set_intensity(28000); rcy.light_component.set_light_color(unreal.LinearColor(0.0,0.8,1.0)); rcy.set_actor_label("RimCyan")
    rmg = eas.spawn_actor_from_class(unreal.RectLight, unreal.Vector( 300,0,120), unreal.Rotator(0,180,0)); rmg.light_component.set_intensity(22000); rmg.light_component.set_light_color(unreal.LinearColor(1.0,0.1,0.7)); rmg.set_actor_label("RimMagenta")
    scan= eas.spawn_actor_from_class(unreal.RectLight, unreal.Vector(0,0,400), unreal.Rotator(-90,0,0)); scan.light_component.set_intensity(60000); scan.light_component.set_light_color(unreal.LinearColor(0.7,0.95,1.0)); scan.set_actor_label("ScanLight"); scan.set_actor_scale3d(unreal.Vector(6,0.05,1))
    fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0,0,-200))
    fc = fog.get_component(); fc.set_editor_property("volumetric_fog", True); fc.set_editor_property("fog_density", 0.06); fc.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.02,0.05,0.09))

    # --- post-process grade: bloom + grain + vignette + DoF + false-color split ---
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0,0,0)); ppv.set_actor_label("PP_Grade")
    ppv.set_editor_property("unbound", True)
    s = ppv.settings
    s.set_editor_property("override_bloom_intensity", True);      s.set_editor_property("bloom_intensity", 2.4)
    s.set_editor_property("override_bloom_threshold", True);      s.set_editor_property("bloom_threshold", 0.8)
    s.set_editor_property("override_vignette_intensity", True);   s.set_editor_property("vignette_intensity", 0.55)
    s.set_editor_property("override_film_grain_intensity", True); s.set_editor_property("film_grain_intensity", 0.28)
    s.set_editor_property("override_auto_exposure_method", True); s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_depth_of_field_fstop", True); s.set_editor_property("depth_of_field_fstop", 2.0)
    # false-color cinematic split: cool shadows, warm/magenta highlights, lifted saturation
    s.set_editor_property("override_color_saturation", True);     s.set_editor_property("color_saturation", unreal.Vector4(1.18,1.18,1.25,1.0))
    s.set_editor_property("override_color_contrast", True);       s.set_editor_property("color_contrast",   unreal.Vector4(1.10,1.10,1.12,1.0))
    s.set_editor_property("override_color_shadows", True);        s.set_editor_property("color_shadows",     unreal.Vector4(0.85,1.0,1.15,1.0))
    s.set_editor_property("override_color_highlights", True);     s.set_editor_property("color_highlights",  unreal.Vector4(1.1,0.95,1.05,1.0))
    ppv.settings = s

    # --- camera (animated in make_sequence.py) ---
    cam = eas.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(0,-620,40), unreal.Rotator(0,90,0)); cam.set_actor_label("HeroCam")
    cc = cam.camera_component
    try: cc.set_editor_property("current_focal_length", 50.0)
    except Exception: pass

    les.save_current_level()
    unreal.log("Map_Protocell built + saved")

if __name__ == "__main__":
    build_level()
