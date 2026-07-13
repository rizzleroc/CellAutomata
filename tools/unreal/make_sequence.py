# make_sequence.py — Unreal 5.8 · build the Level Sequence for the hero cut.
# Camera slow push-in (creeping microscope), the cell division (parent pinches -> two daughters separate),
# and the one-time scan-light sweep. 120 frames @ 24fps = 5.0s, loop-friendly. Run after build_scene.py.
import unreal

PKG, MAP = "/Game/Protocell", "/Game/Protocell/Map_Protocell"
SEQ = f"{PKG}/SEQ_Protocell"
FPS, NF = 24, 120
AT, EAL = unreal.AssetToolsHelpers.get_asset_tools(), unreal.EditorAssetLibrary

def actor(label):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label: return a
    raise RuntimeError(f"actor not found: {label} (run build_scene.py first)")

def fr(f): return unreal.FrameNumber(int(f))

def key_transform(seq, a, keys):
    """keys: list of (frame, loc(x,y,z), scale s) -> animate Location + uniform Scale."""
    b = seq.add_possessable(a)
    tr = b.add_track(unreal.MovieScene3DTransformTrack)
    sec = tr.add_section(); sec.set_range(0, NF)
    ch = sec.get_channels()  # [Lx,Ly,Lz, Rx,Ry,Rz, Sx,Sy,Sz]
    for (f, loc, s) in keys:
        ch[0].add_key(fr(f), float(loc[0])); ch[1].add_key(fr(f), float(loc[1])); ch[2].add_key(fr(f), float(loc[2]))
        ch[6].add_key(fr(f), float(s));      ch[7].add_key(fr(f), float(s));      ch[8].add_key(fr(f), float(s))
    return b

def build():
    if EAL.does_asset_exist(SEQ): EAL.delete_asset(SEQ)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    seq = AT.create_asset("SEQ_Protocell", PKG, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(FPS, 1)); seq.set_playback_start(0); seq.set_playback_end(NF)

    # camera: creeping push-in (Y -620 -> -360), tiny rise; bind as the active camera cut
    cam = actor("HeroCam")
    cb = key_transform(seq, cam, [(0,(0,-620,40),1.0),(NF,(0,-360,70),1.0)])
    try:    cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
    except Exception: cut = seq.add_master_track(unreal.MovieSceneCameraCutTrack)
    cs = cut.add_section(); cs.set_range(0, NF)
    bid = unreal.MovieSceneObjectBindingID(); bid.set_editor_property("guid", cb.get_id())
    cs.set_camera_binding_id(bid)

    # division: parent swells then pinches to nothing; daughters emerge and separate
    key_transform(seq, actor("ParentCell"), [(0,(0,0,0),1.6),(48,(0,0,0),2.05),(84,(0,0,0),1.2),(NF,(0,0,0),0.05)])
    key_transform(seq, actor("DaughterA"),  [(0,(0,0,0),0.02),(60,(-20,0,0),0.3),(NF,(-150,0,0),1.5)])
    key_transform(seq, actor("DaughterB"),  [(0,(0,0,0),0.02),(60,( 20,0,0),0.3),(NF,( 150,0,0),1.5)])

    # scan-sweep: ScanLight drops from +420 to -420 across frames 18..54 (a single luminous pass)
    sl = actor("ScanLight")
    b = seq.add_possessable(sl); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF); ch = sec.get_channels()
    for f, z in [(0,420),(18,420),(54,-420),(NF,-420)]: ch[2].add_key(fr(f), float(z))

    EAL.save_asset(SEQ)
    unreal.log(f"SEQ_Protocell built: {NF}f @ {FPS}fps ({NF/FPS:.1f}s)")

if __name__ == "__main__":
    build()
