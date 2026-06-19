# render.py — Unreal 5.8 · render SEQ_Protocell to a 1080x1920 24fps frame sequence via Movie Render Queue.
# Run after build_scene.py + make_sequence.py. In-editor: kicks the PIE executor. Headless: see run_ue.sh.
# NOTE: UE 5.8 ships Movie Render GRAPH as the newer system; this uses the stable Movie Render QUEUE
# (MoviePipeline*) API. If your build removed it, port the settings to a render-graph asset (same values).
import unreal, os

PKG = "/Game/Protocell"
MAP = f"{PKG}/Map_Protocell"
SEQ = f"{PKG}/SEQ_Protocell"
OUT_DIR = os.environ.get("UE_OUT_DIR", "{project_dir}/Saved/MovieRenders/protocell")

def configure(job):
    job.map = unreal.SoftObjectPath(MAP)
    job.sequence = unreal.SoftObjectPath(SEQ)
    cfg = job.get_configuration()
    out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out.output_resolution = unreal.IntPoint(1080, 1920)                 # true vertical
    out.output_directory  = unreal.DirectoryPath(OUT_DIR)
    out.file_name_format  = "protocell.{frame_number}"
    out.use_custom_frame_rate = True
    out.output_frame_rate = unreal.FrameRate(24, 1)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)  # PNG seq -> mux with ffmpeg (see README)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("override_anti_aliasing", True)
    aa.set_editor_property("spatial_sample_count", 2)
    aa.set_editor_property("temporal_sample_count", 8)                  # clean motion blur on the push-in + division
    try: aa.set_editor_property("anti_aliasing_method", unreal.AntiAliasingMethod.AAM_TSR)
    except Exception: pass

def main():
    sub = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = sub.get_queue(); q.delete_all_jobs()
    configure(q.allocate_new_job(unreal.MoviePipelineExecutorJob))
    unreal.log(f"MRQ queued -> {OUT_DIR} @ 1080x1920/24. Rendering...")
    sub.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)     # headless executor runs + exits via run_ue.sh

if __name__ == "__main__":
    main()
