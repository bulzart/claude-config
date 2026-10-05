import json, sys, time
from scenedetect import open_video, SceneManager, ContentDetector, AdaptiveDetector
src, out = sys.argv[1], sys.argv[2]
res = {}
for name, det in [("content_t27", ContentDetector(threshold=27.0, min_scene_len=6)),
                  ("adaptive_t3", AdaptiveDetector(adaptive_threshold=3.0, min_scene_len=6))]:
    t = time.time()
    video = open_video(src)
    sm = SceneManager(); sm.add_detector(det)
    sm.detect_scenes(video, show_progress=False)
    scenes = sm.get_scene_list()
    res[name] = {"elapsed_s": round(time.time() - t, 2), "n_scenes": len(scenes),
                 "scenes": [{"i": i + 1, "start": round(s.get_seconds(), 3), "end": round(e.get_seconds(), 3),
                             "start_frame": s.get_frames(), "end_frame": e.get_frames(),
                             "dur": round(e.get_seconds() - s.get_seconds(), 3)} for i, (s, e) in enumerate(scenes)]}
json.dump(res, open(out, "w"), indent=1)
for k, v in res.items():
    print(k, v["n_scenes"], "scenes in", v["elapsed_s"], "s")
    for sc in v["scenes"]:
        print("  ", sc["i"], f"{sc['start']:.3f}-{sc['end']:.3f} ({sc['dur']}s) frames {sc['start_frame']}-{sc['end_frame']}")
