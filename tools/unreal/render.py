"""
render.py — STAGE 4 of the protocell UE 5.8 pipeline.

Renders LS_ProtocellHero to a vertical 1080x1920 / 24fps PNG sequence.

Two modes (UE_RENDER_MODE=mrq|flipbook):
  mrq       (default) — Movie Render Queue render of the sequence. The
            per-frame visibility tracks (make_sequence.py) cleave the cell;
            camera push-in and scan-sweep animate. Full quality + motion blur.
  flipbook  — show exactly one Cleave_ mesh per frame in Python, scrub the
            sequence, screenshot each frame. Robust fallback that needs no
            visibility tracks; every frame is a real 3D isosurface.

============================ VERSION-SENSITIVE ============================
FLAG-R : UE 5.8 ships the new RENDER GRAPH alongside classic Movie Render
         Queue. The MoviePipeline* API below is the CLASSIC MRQ path (still in
         5.8). If your studio standard is the Render Graph, swap the queue
         construction for a graph preset; res/fps/output/PNG settings map 1:1.
FLAG-X : Headless executor = MoviePipelinePIEExecutor (fine for
         -ExecutePythonScript). Some builds expose MoviePipelineNewProcessExecutor.
==========================================================================
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pcfg  # noqa: E402

import unreal  # noqa: E402

MODE = os.environ.get("UE_RENDER_MODE", "mrq").lower()


def _configure_mrq_job(job):
    """Apply res / fps / output / PNG settings to an MRQ job. FLAG-R."""
    cfg = job.get_configuration()

    out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out.output_resolution = unreal.IntPoint(pcfg.RES_X, pcfg.RES_Y)
    out.output_directory = unreal.DirectoryPath(pcfg.OUTPUT_DIR)
    out.file_name_format = "protocell.{frame_number}"
    out.output_frame_rate = unreal.FrameRate(pcfg.FPS, 1)
    out.override_existing_output = True
    out.zero_pad_frame_numbers = 4

    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.spatial_sample_count = 4
    aa.temporal_sample_count = 2


def render_mrq():
    pcfg.banner("STAGE 4 — Movie Render Queue (%dx%d @ %dfps)"
                % (pcfg.RES_X, pcfg.RES_Y, pcfg.FPS))
    os.makedirs(pcfg.OUTPUT_DIR, exist_ok=True)

    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    queue = subsystem.get_queue()
    queue.delete_all_jobs()

    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.map = unreal.SoftObjectPath("%s/%s" % (pcfg.LEVEL_PATH, pcfg.LEVEL_NAME))
    job.sequence = unreal.SoftObjectPath("%s/%s" % (pcfg.SEQ_PATH, pcfg.SEQ_HERO))
    _configure_mrq_job(job)

    executor = unreal.MoviePipelinePIEExecutor()  # FLAG-X
    subsystem.render_queue_with_executor_instance(executor)
    unreal.log("[render] MRQ submitted -> %s" % pcfg.OUTPUT_DIR)


def _cleave_actors():
    out = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl.startswith("Cleave_"):
            out.append((int(lbl.split("_")[1]), a))
    out.sort(key=lambda t: t[0])
    return [a for _, a in out]


def render_flipbook():
    """Real-division render (3D mesh path): show exactly one Cleave_ mesh per
    frame, scrub the sequence (camera + scan), and screenshot. Every frame is a
    real 3D Gray-Scott isosurface, so the cell genuinely cleaves."""
    pcfg.banner("STAGE 4 — flipbook render (real per-frame cleavage)")
    os.makedirs(pcfg.OUTPUT_DIR, exist_ok=True)

    actors = _cleave_actors()
    if not actors:
        unreal.log_warning("[render] no Cleave_ actors — run build_scene.py")
        return

    player = unreal.LevelSequenceEditorBlueprintLibrary  # FLAG-R: open + scrub
    player.open_level_sequence(
        unreal.SoftObjectPath("%s/%s" % (pcfg.SEQ_PATH, pcfg.SEQ_HERO)))

    n = min(len(actors), pcfg.FRAME_COUNT)
    for f in range(n):
        for i, a in enumerate(actors):
            a.set_actor_hidden_in_game(i != f)
        player.set_current_time(f)
        out = os.path.join(pcfg.OUTPUT_DIR, "protocell.%04d.png" % f)
        unreal.AutomationLibrary.take_high_res_screenshot(
            pcfg.RES_X, pcfg.RES_Y, out)
        unreal.log("[render] frame %04d -> %s" % (f, out))
    unreal.log("[render] flipbook DONE (%d frames)" % n)


def main():
    if MODE == "flipbook":
        render_flipbook()
    else:
        render_mrq()


if __name__ == "__main__":
    main()
