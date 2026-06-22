"""
make_sequence.py — STAGE 3 of the protocell UE 5.8 pipeline (mesh-sequence).

Builds LS_ProtocellHero, the 3-second / 72-frame vertical Level Sequence over
the cleavage:
  * camera slow push-in onto the dividing cell
  * the scan-sweep sheet translating across frame
  * per-frame VISIBILITY tracks that reveal exactly one Cleave_NNNN mesh per
    frame (so the cell cleaves on screen in an MRQ render)

The per-frame reveal is what makes the real 3D division play back. If you use
render.py's "flipbook" mode instead, it toggles the same actors in Python and
you can skip the visibility tracks (set BUILD_VIS=0).

Run after build_scene.py.

============================ VERSION-SENSITIVE ============================
FLAG-S   : Sequencer channel access (get_channels()[i].add_key) + FrameNumber.
FLAG-VIS : MovieSceneVisibilityTrack keys the actor's "Hidden" flag — on most
           5.x builds a key VALUE of False = VISIBLE (hidden=false). If your
           cells show inverted (all hidden / all shown), flip VIS_SHOWN below.
==========================================================================
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pcfg  # noqa: E402

import unreal  # noqa: E402

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

BUILD_VIS = os.environ.get("UE_BUILD_VIS", "1") != "0"
VIS_SHOWN = False   # FLAG-VIS: value that means "visible" (hidden=False)


def _frame(n):
    return unreal.FrameNumber(int(n))


def _find(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def _all_cleave_actors():
    out = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl.startswith("Cleave_"):
            out.append((int(lbl.split("_")[1]), a))
    out.sort(key=lambda t: t[0])
    return out


def create_sequence():
    pcfg.banner("STAGE 3 — level sequence (cleavage + push-in + scan)")

    seq = TOOLS.create_asset(pcfg.SEQ_HERO, pcfg.SEQ_PATH,
                             unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    fps = pcfg.FPS
    seq.set_display_rate(unreal.FrameRate(fps, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(pcfg.FRAME_COUNT)

    # ---- camera push-in -----------------------------------------------------
    cam = _find("HeroCamera")
    if cam:
        cb = seq.add_possessable(cam)
        tt = cb.add_track(unreal.MovieScene3DTransformTrack)
        ts = tt.add_section()
        ts.set_range(0, pcfg.FRAME_COUNT)
        ch = ts.get_channels()  # FLAG-S: [Tx,Ty,Tz,Rx,Ry,Rz,Sx,Sy,Sz]
        ch[0].add_key(_frame(0), 0.0)
        ch[1].add_key(_frame(0), -230.0)
        ch[2].add_key(_frame(0), 36.0)
        ch[1].add_key(_frame(pcfg.FRAME_COUNT), -150.0)  # push in
        ch[2].add_key(_frame(pcfg.FRAME_COUNT), 22.0)
        for c in (0,):
            ch[c].add_key(_frame(pcfg.FRAME_COUNT), 0.0)
        cut = seq.add_master_track(unreal.MovieSceneCameraCutTrack)
        cs = cut.add_section()
        cs.set_range(0, pcfg.FRAME_COUNT)
        cs.set_camera_binding_id(cb.get_binding_id())

    # ---- scan-sweep ---------------------------------------------------------
    scan = _find("ScanSweep")
    if scan:
        sb = seq.add_possessable(scan)
        st = sb.add_track(unreal.MovieScene3DTransformTrack)
        ss = st.add_section()
        ss.set_range(0, pcfg.FRAME_COUNT)
        sch = ss.get_channels()
        sch[0].add_key(_frame(0), -180.0)
        sch[0].add_key(_frame(pcfg.FRAME_COUNT), 180.0)
        sch[1].add_key(_frame(0), -40.0)
        sch[2].add_key(_frame(0), 0.0)

    # ---- per-frame cleavage reveal -----------------------------------------
    if BUILD_VIS:
        actors = _all_cleave_actors()
        n = len(actors)
        if n:
            span = max(1, pcfg.FRAME_COUNT // n)
            for idx, (fi, a) in enumerate(actors):
                b = seq.add_possessable(a)
                vt = b.add_track(unreal.MovieSceneVisibilityTrack)  # FLAG-VIS
                vs = vt.add_section()
                vs.set_range(0, pcfg.FRAME_COUNT)
                vch = vs.get_channels()[0]
                start = idx * span
                end = pcfg.FRAME_COUNT if idx == n - 1 else (idx + 1) * span
                # hidden everywhere, shown only across this frame's slice
                vch.add_key(_frame(0), not VIS_SHOWN)
                vch.add_key(_frame(start), VIS_SHOWN)
                vch.add_key(_frame(end), not VIS_SHOWN)
            unreal.log("[seq] keyed visibility for %d cleavage frames" % n)
        else:
            unreal.log_warning("[seq] no Cleave_ actors found — run build_scene.py")

    EAL.save_loaded_asset(seq)
    unreal.log("[seq] DONE  %s (%d frames @ %dfps)"
               % (pcfg.SEQ_HERO, pcfg.FRAME_COUNT, fps))
    return seq


if __name__ == "__main__":
    create_sequence()
