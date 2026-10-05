"""build_capcut_draft.py — edit-plan.json -> CapCut 9.4 draft folder (seeded from a real 9.4 draft).

    python build_capcut_draft.py <edit-plan.json> --name <draft-name>
        [--drafts-dir DIR]        CapCut draft store (default: the live store
                                  C:\\Users\\Glaresquare1\\AppData\\Local\\CapCut\\User Data\\Projects\\com.lveditor.draft)
        [--template DIR]          app-authored 9.4 draft used as the template
                                  (default: research\\capcut-draft-sample)
        [--project-copy DIR]      where our own copy of the draft is kept (default <plan dir>\\project\\capcut\\<name>)
        [--no-register]           do not touch root_meta_info.json (the draft folder is still written)
        [--timelines-mirror]      also write Timelines\\project.json + Timelines\\<id>\\draft_content.json
                                  (off by default: CapCut 8.4-9.3 materialise the nested copy from the root
                                  documents on first open — capcut-cli version-support.md; opt in if CapCut
                                  opens an empty timeline)
        [--force]                 write into the live store even while CapCut.exe is running (never advised)
        [--no-lint]               skip `capcut lint` / `capcut version` (capcut-cli 0.23)
        [--json]                  print the build report as JSON

What is written (all from the plan, ids fresh, every other field copied verbatim from the template so the
version markers are CapCut 9.4's own: version 360000, new_version "185.0.0", platform.app_version "9.4.0"):
  draft_content.json      canvas 1080x1920 (ratio 9:16) 30 fps; main video track = one segment per clip piece
                          (trims, order, speed; a speed_ramps clip becomes consecutive segments); transitions
                          (Dissolve / Slide / Pull in, from capcut-cli's enum catalogue) attached to the first
                          segment of each pair; audio tracks for the music bed and the SFX; ONE text track with
                          hook / callout / end-card overlays (never speech captions); PNG stickers on a second
                          video track as photo materials.
  draft_meta_info.json    draft identity + draft_materials[type 0] entry per media file (absolute path, µs
                          duration, size) - the list CapCut 9.x consults to resolve local clips
                          (videos[].local_material_id = that entry's id).
  draft_virtual_store.json, draft_settings, timeline_layout.json, key_value.json, draft_agency_config.json,
  performance_opt_info.json, attachment_pc_common.json, draft_cover.jpg (first frame), empty resource dirs.
  root_meta_info.json     (drafts dir) backed up to root_meta_info.json.bak-<stamp> first; our entry appended
                          (or replaced when the same draft name was built before); other drafts untouched.
  build-report.json + lint.json inside the draft folder.

Validation: JSON re-parses; every segment.material_id / extra_material_refs id exists; timeline duration ==
last segment end; every media path exists; `capcut lint` + `capcut version` output recorded (capcut-cli).

Timing model: CapCut keeps main-track segments contiguous, so the draft's duration is the SUM of the clip
pieces; the ffmpeg render overlaps each transition (xfade), so final.mp4 is shorter by the sum of the
transition durations. Quantised to the 30 fps grid (CapCut re-snaps durations on first open anyway).

Exit codes: 0 ok, 1 plan/usage error, 2 build or validation failure, 3 refused (caption-shaped plan),
4 CapCut is running on the live store (use --force or close CapCut).
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_edit as ce  # noqa: E402

US = 1_000_000

# capcut-cli 0.23 `capcut enums --transitions` (CapCut namespace), read 2026-09-16 on this machine.
CAPCUT_TRANSITIONS = {
    "xfade": {"slug": "dissolve", "name": "Dissolve", "effect_id": "392FD26E-A514-4d0f-8950-EA4A20CB407C",
              "resource_id": "6724846004274729480", "is_overlap": False},
    "whip": {"slug": "slide", "name": "Slide", "effect_id": "AF0D3666-48D3-4ff0-B836-EB93B174A74A",
             "resource_id": "6757982416649851399", "is_overlap": False},
    "zoom": {"slug": "pull-in", "name": "Pull in", "effect_id": "E27206B3-FFA0-4ea4-B6E7-44350CED4574",
             "resource_id": "6724226861666144779", "is_overlap": False},
}

TEMPLATE_FILES_VERBATIM = ["draft_agency_config.json", "key_value.json", "performance_opt_info.json",
                           "attachment_pc_common.json"]
EMPTY_DIRS = ["Resources", "Resources/audioAlg", "Resources/videoAlg", "adjust_mask", "matting", "qr_upload",
              "smart_crop", "subdraft", "common_attachment"]


def us(seconds: float, fps: int) -> int:
    """Seconds -> microseconds snapped to the frame grid (round to nearest frame)."""
    frames = int(round(float(seconds) * fps))
    return int(round(frames * US / fps))


def fwd(p: str) -> str:
    return os.path.abspath(p).replace("\\", "/")


def hex_to_rgb01(h: str) -> list[float]:
    h = (h or "#FFFFFF").lstrip("#")
    if len(h) != 6:
        h = "FFFFFF"
    return [round(int(h[i:i + 2], 16) / 255.0, 4) for i in (0, 2, 4)]


class DraftBuilder:
    def __init__(self, plan: dict, base: str, template_dir: str, name: str, drafts_dir: str, fps: int):
        self.plan, self.base, self.template_dir, self.name, self.drafts_dir, self.fps = plan, base, template_dir, name, drafts_dir, fps
        self.W, self.H = int(plan["project"]["width"]), int(plan["project"]["height"])
        self.tpl = ce.load_json(os.path.join(template_dir, "draft_content.json"))
        self.tpl_meta = ce.load_json(os.path.join(template_dir, "draft_meta_info.json"))
        self.tpl_video_mat = self.tpl["materials"]["videos"][0]
        vt = next(t for t in self.tpl["tracks"] if t["type"] == "video")
        self.tpl_track = vt
        self.tpl_seg = vt["segments"][0]
        self.tpl_companions = {}
        for cat in ("speeds", "placeholder_infos", "canvases", "sound_channel_mappings", "material_colors", "vocal_separations"):
            self.tpl_companions[cat] = self.tpl["materials"][cat][0]
        self.materials = {k: [] for k in self.tpl["materials"].keys()}
        self.tracks: list[dict] = []
        self.meta_media: dict[str, dict] = {}   # abs path -> draft_materials entry
        self.warnings: list[str] = []
        self.timeline_id = ce.capcut_uuid()
        self.draft_id = ce.capcut_uuid()
        self.now_s = int(time.time())
        self.now_us = int(time.time() * US)

    # ------------------------------------------------------------------ materials helpers
    def _companion(self, cat: str, **over) -> str:
        m = copy.deepcopy(self.tpl_companions[cat])
        m["id"] = ce.capcut_uuid()
        m.update(over)
        self.materials[cat].append(m)
        return m["id"]

    def _register_media(self, path: str, probe: dict, metetype: str) -> dict:
        path = os.path.abspath(path)
        if path in self.meta_media:
            return self.meta_media[path]
        e = {"ai_group_type": "", "create_time": self.now_s, "duration": int(round(probe["duration"] * US)),
             "enter_from": 0, "extra_info": os.path.basename(path), "file_Path": fwd(path),
             "height": int(probe.get("height") or 0), "id": ce.plain_uuid(), "import_time": self.now_s,
             "import_time_ms": self.now_us, "item_source": 1, "material_color_tag": "", "md5": "",
             "metetype": metetype, "roughcut_time_range": {"duration": int(round(probe["duration"] * US)), "start": 0},
             "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": int(probe.get("width") or 0),
             "_size": int(probe.get("size") or 0)}
        self.meta_media[path] = e
        return e

    def _video_material(self, path: str, probe: dict, kind: str = "video") -> str:
        m = copy.deepcopy(self.tpl_video_mat)
        entry = self._register_media(path, probe, "video" if kind == "video" else "photo")
        m.update({"id": ce.capcut_uuid(), "unique_id": "", "type": kind, "duration": int(round(probe["duration"] * US)) if kind == "video" else 10_800_000_000,
                  "path": fwd(path), "material_name": os.path.basename(path), "width": int(probe.get("width") or 0),
                  "height": int(probe.get("height") or 0), "has_audio": bool(probe.get("has_audio")),
                  "local_material_id": entry["id"], "category_name": "local"})
        self.materials["videos"].append(m)
        return m["id"]

    def _audio_material(self, path: str, probe: dict, atype: str = "extract_music") -> str:
        entry = self._register_media(path, probe, "music")
        m = {"app_id": 0, "category_id": "", "category_name": "local", "check_flag": 1, "copyright_limit_type": "none",
             "duration": int(round(probe["duration"] * US)), "effect_id": "", "formula_id": "", "id": ce.capcut_uuid(),
             "intensifies_path": "", "is_ai_clone_tone": False, "is_text_edit_overdub": False, "is_ugc": False,
             "local_material_id": entry["id"], "music_id": "", "name": os.path.basename(path), "path": fwd(path),
             "query": "", "request_id": "", "resource_id": "", "search_id": "", "source_from": "", "source_platform": 0,
             "team_id": "", "text_id": "", "tone_category_id": "", "tone_category_name": "", "tone_effect_id": "",
             "tone_effect_name": "", "tone_platform": "", "tone_second_category_id": "", "tone_second_category_name": "",
             "tone_speaker": "", "tone_type": "", "type": atype, "video_id": "", "wave_points": []}
        self.materials["audios"].append(m)
        return m["id"]

    def _transition_material(self, ttype: str, duration_s: float) -> str | None:
        spec = CAPCUT_TRANSITIONS.get(ttype)
        if not spec:
            return None
        m = {"id": ce.capcut_uuid(), "type": "transition", "name": spec["name"], "effect_id": spec["effect_id"],
             "resource_id": spec["resource_id"], "duration": us(duration_s, self.fps), "is_overlap": spec["is_overlap"],
             "category_id": "", "category_name": "", "platform": "all", "path": "", "source_platform": 1,
             "formula_id": "", "request_id": "", "material_type": ""}
        self.materials["transitions"].append(m)
        return m["id"]

    # ------------------------------------------------------------------ segments
    def _video_segment(self, material_id: str, src_a: float, src_b: float, speed: float, t_start_us: int,
                       transform: dict | None, volume: float, extra_refs: list[str] | None = None,
                       render_index: int = 0) -> dict:
        s = copy.deepcopy(self.tpl_seg)
        tgt_dur = us((src_b - src_a) / speed, self.fps)
        src_dur = int(round(tgt_dur * speed))
        refs = [self._companion("speeds", speed=float(speed)), self._companion("placeholder_infos"),
                self._companion("canvases"), self._companion("sound_channel_mappings"),
                self._companion("material_colors"), self._companion("vocal_separations")]
        if extra_refs:
            refs += extra_refs
        tr = transform or {}
        sc = max(1.0, float(tr.get("scale", 1.0) or 1.0))
        if tr.get("fit") == "contain":
            sc = 1.0  # CapCut fits the source inside the canvas at scale 1.0 (letterbox = contain)
        elif sc == 1.0:
            # cover-fit: scale the fitted source until it fills the canvas
            sc = 1.0
        x_norm = float(tr.get("x", 0.0) or 0.0) / (self.W / 2.0)
        y_norm = -float(tr.get("y", 0.0) or 0.0) / (self.H / 2.0)
        s.update({"id": ce.capcut_uuid(), "material_id": material_id,
                  "source_timerange": {"start": us(src_a, self.fps), "duration": src_dur},
                  "target_timerange": {"start": t_start_us, "duration": tgt_dur},
                  "speed": float(speed), "volume": float(volume), "last_nonzero_volume": float(volume) or 1.0,
                  "extra_material_refs": refs, "render_index": render_index})
        s["clip"] = {"scale": {"x": sc, "y": sc}, "rotation": 0.0, "transform": {"x": round(x_norm, 4), "y": round(y_norm, 4)},
                     "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0}
        s["uniform_scale"] = {"on": True, "value": sc}
        return s

    def _audio_segment(self, material_id: str, src_a: float, src_b: float, t_start_us: int, volume: float) -> dict:
        s = copy.deepcopy(self.tpl_seg)
        dur = us(src_b - src_a, self.fps)
        refs = [self._companion("speeds", speed=1.0), self._companion("placeholder_infos"),
                self._companion("sound_channel_mappings"), self._companion("vocal_separations")]
        s.update({"id": ce.capcut_uuid(), "material_id": material_id,
                  "source_timerange": {"start": us(src_a, self.fps), "duration": dur},
                  "target_timerange": {"start": t_start_us, "duration": dur},
                  "speed": 1.0, "volume": float(volume), "last_nonzero_volume": float(volume) or 1.0,
                  "extra_material_refs": refs, "render_index": 0, "clip": None, "uniform_scale": None,
                  "hdr_settings": None, "enable_lut": False, "enable_adjust": False})
        return s

    def _text_material(self, item: dict) -> str:
        preset = item["preset"]
        text = "\n".join(item["lines"])
        size_px = int(item["size"])
        cc_size = max(4, int(round(size_px / 4.6)))      # heuristic: capcut-cli hook template = 19 at ~88 px
        fill = hex_to_rgb01(preset.get("fill", "#FFFFFF"))
        hl = {w.lower().strip(".,!?") for w in item.get("highlight_words") or []}
        hl_rgb = hex_to_rgb01(item.get("highlight_colour") or "#FFE600")
        font_obj = {"id": "", "path": fwd(item["font_path"])} if item.get("font_path") else {"id": "", "path": ""}

        def style(a: int, b: int, rgb: list[float], size: int) -> dict:
            return {"range": [a, b], "size": size, "bold": bool(preset.get("bold")), "italic": False, "underline": False,
                    "fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": rgb}}},
                    "font": font_obj,
                    "strokes": [{"content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": hex_to_rgb01(preset.get("outline_colour", "#000000"))}},
                                 "width": round(float(preset.get("outline", 4)) / max(size_px, 1), 3)}]}

        # ranges in UTF-16 code units (capcut-cli docs; the "text disappeared" bug source)
        styles = []
        pos = 0
        sub_size = max(4, int(round(int(preset.get("sub_size", 60)) / 4.6))) if item["type"] == "end_card" else cc_size
        for li, line in enumerate(item["lines"]):
            line_size = sub_size if (li > 0 and item["type"] == "end_card") else cc_size
            for wi, w in enumerate(line.split(" ")):
                if wi > 0:
                    styles.append(style(pos, pos + 1, fill, line_size)); pos += 1
                n = ce.utf16_len(w)
                rgb = hl_rgb if (hl and w.lower().strip(".,!?") in hl) else fill
                styles.append(style(pos, pos + n, rgb, line_size)); pos += n
            if li < len(item["lines"]) - 1:
                styles.append(style(pos, pos + 1, fill, line_size)); pos += 1
        # merge adjacent identical-style ranges
        merged = []
        for st in styles:
            if merged and merged[-1]["fill"] == st["fill"] and merged[-1]["size"] == st["size"] and merged[-1]["range"][1] == st["range"][0]:
                merged[-1]["range"][1] = st["range"][1]
            else:
                merged.append(st)
        content = {"styles": merged, "text": text, "layer_weight": 1, "effect": []}
        m = {"id": ce.capcut_uuid(), "type": "text", "content": json.dumps(content, ensure_ascii=False, separators=(",", ":")),
             "alignment": 1, "font_size": cc_size, "text_color": preset.get("fill", "#FFFFFF").upper(), "text_alpha": 1.0,
             "typesetting": 0, "letter_spacing": 0.0, "line_spacing": 0.02, "line_feed": 1, "line_max_width": 0.82,
             "force_apply_line_max_width": False, "check_flag": 7, "fixed_width": -1.0, "fixed_height": -1.0,
             "has_shadow": bool(preset.get("shadow", 0)), "shadow_alpha": 0.8, "shadow_angle": -45.0,
             "shadow_color": "#000000", "shadow_distance": float(max(2, int(preset.get("shadow", 0)) * 2)), "shadow_smoothing": 1.0,
             "border_width": round(float(preset.get("outline", 4)) / max(size_px, 1), 3),
             "border_color": preset.get("outline_colour", "#000000").upper(), "border_alpha": 1.0, "has_border": bool(preset.get("outline", 0)),
             "background_color": "#000000", "background_alpha": 0.0, "background_style": 0, "background_round_radius": 0.0,
             "background_width": 0.14, "background_height": 0.14, "background_horizontal_offset": 0.0, "background_vertical_offset": 0.0,
             "font_name": item["font"], "font_path": fwd(item["font_path"]) if item.get("font_path") else "",
             "font_id": "", "font_resource_id": "", "font_category_id": "", "font_category_name": "", "font_source_platform": 0,
             "font_team_id": "", "font_title": "none", "font_url": "", "fonts": [],
             "global_alpha": 1.0, "group_id": "", "is_rich_text": False, "use_effect_default_color": False,
             "text_size": 30, "text_to_audio_ids": [], "tts_auto_update": False, "underline": False, "vertical": False,
             "italic_degree": 0, "ktv_color": "", "language": "", "layer_weight": 1, "multi_language_current": "none",
             "name": "", "preset_category": "", "preset_category_id": "", "preset_has_set_alignment": False, "preset_id": "",
             "preset_index": 0, "preset_name": "", "recognize_task_id": "", "recognize_type": 0, "relevance_segment": [],
             "shape_clip_x": False, "shape_clip_y": False, "source_from": "", "style_name": "", "sub_type": 0,
             "subtitle_keywords": None, "subtitle_template_original_fontsize": 0.0, "template_id": "", "words": {"end_time": [], "start_time": [], "text": []}}
        self.materials["texts"].append(m)
        return m["id"]

    def _text_segment(self, material_id: str, item: dict) -> dict:
        s = copy.deepcopy(self.tpl_seg)
        t0, t1 = us(item["t_start"], self.fps), us(item["t_end"], self.fps)
        refs = [self._companion("speeds", speed=1.0), self._companion("placeholder_infos"),
                self._companion("sound_channel_mappings"), self._companion("vocal_separations")]
        x_norm = (float(item["x"]) - self.W / 2.0) / (self.W / 2.0)
        y_norm = (self.H / 2.0 - float(item["y"])) / (self.H / 2.0)
        s.update({"id": ce.capcut_uuid(), "material_id": material_id,
                  "source_timerange": {"start": 0, "duration": t1 - t0},
                  "target_timerange": {"start": t0, "duration": t1 - t0},
                  "speed": 1.0, "volume": 1.0, "extra_material_refs": refs, "render_index": 15000,
                  "track_render_index": 0, "enable_lut": False, "enable_adjust": False, "hdr_settings": None})
        s["clip"] = {"scale": {"x": 1.0, "y": 1.0}, "rotation": 0.0, "transform": {"x": round(x_norm, 4), "y": round(y_norm, 4)},
                     "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0}
        s["uniform_scale"] = {"on": True, "value": 1.0}
        return s

    def _track(self, ttype: str, segments: list[dict], name: str = "") -> dict:
        t = copy.deepcopy(self.tpl_track)
        t.update({"id": ce.capcut_uuid(), "type": ttype, "segments": segments, "name": name, "is_default_name": not name})
        return t

    # ------------------------------------------------------------------ build
    def build(self, probes: dict, placed: list[dict], total_render: float) -> dict:
        plan = self.plan
        # main video track
        segs = []
        cursor = 0
        trans = ce.transition_lookup(plan)
        order = [p["clip"] for p in placed]
        capcut_total = 0
        for i, p in enumerate(placed):
            c = p["clip"]
            path = ce.resolve_path(c["path"], self.base)
            pr = probes[path]
            mat = self._video_material(path, pr, "video")
            nxt = order[i + 1] if i + 1 < len(order) else None
            tr_id = None
            if nxt is not None:
                t = trans.get((c["id"], nxt["id"]))
                if t and t.get("type", "cut") != "cut":
                    name, dflt = ce.XFADE_MAP.get(t["type"], ("fade", 0.4))
                    tr_id = self._transition_material(t["type"], float(t.get("duration", dflt) or dflt))
            pieces = p["pieces"]
            for j, (a, b, s) in enumerate(pieces):
                seg = self._video_segment(mat, a, b, s, cursor, c.get("transform"),
                                          float(c.get("volume", 1.0) if c.get("volume") is not None else 1.0),
                                          extra_refs=[tr_id] if (tr_id and j == len(pieces) - 1) else None)
                seg["_plan_clip"] = c["id"]
                cursor += seg["target_timerange"]["duration"]
                segs.append(seg)
        capcut_total = cursor
        self.tracks.append(self._track("video", segs))
        # sticker PNGs -> photo materials on an overlay video track
        stk_segs = []
        for ov in plan.get("text_overlays") or []:
            if ov.get("type") == "sticker" and ov.get("image"):
                ip = ce.resolve_path(ov["image"], self.base)
                if not (ip and os.path.isfile(ip)):
                    self.warnings.append(f"sticker image missing: {ip}")
                    continue
                try:
                    from PIL import Image
                    with Image.open(ip) as im:
                        iw, ih = im.size
                except Exception:
                    iw, ih = 0, 0
                pr = {"duration": 5.0, "width": iw, "height": ih, "has_audio": False, "size": os.path.getsize(ip)}
                mat = self._video_material(ip, pr, "photo")
                t0, t1 = float(ov.get("t_start", 0)), float(ov.get("t_end", total_render))
                pos = ov.get("position") or {}
                seg = self._video_segment(mat, 0.0, max(0.1, t1 - t0), 1.0, us(t0, self.fps), None, 0.0, render_index=14000)
                want_w = float(ov.get("width_px") or 300)
                # CapCut fits the photo to the canvas at scale 1.0 (UNCERTAIN convention) -> scale = wanted / fitted width
                fitted_w = self.W if (iw and ih and iw / ih >= self.W / self.H) else (self.H * iw / ih if ih else self.W)
                sc = round(want_w / fitted_w, 4) if fitted_w else 1.0
                x_norm = (float(pos.get("x_px", self.W / 2)) - self.W / 2.0) / (self.W / 2.0)
                y_norm = (self.H / 2.0 - float(pos.get("y_px", self.H / 2))) / (self.H / 2.0)
                seg["clip"] = {"scale": {"x": sc, "y": sc}, "rotation": 0.0, "transform": {"x": round(x_norm, 4), "y": round(y_norm, 4)},
                               "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0}
                seg["uniform_scale"] = {"on": True, "value": sc}
                stk_segs.append(seg)
        if stk_segs:
            self.tracks.append(self._track("video", stk_segs, "stickers"))
        # audio: music bed + sfx
        audio = plan.get("audio") or {}
        music = audio.get("music") or {}
        mp = ce.resolve_path(music.get("path"), self.base) if music.get("path") else None
        if mp and os.path.isfile(mp):
            pr = ce.probe_media(mp)
            mat = self._audio_material(mp, pr, "extract_music")
            start = float(music.get("start", 0.0) or 0.0)
            length = min(pr["duration"], max(0.0, capcut_total / US - start))
            if length > 0:
                seg = self._audio_segment(mat, 0.0, length, us(start, self.fps), ce.db_to_lin(ce.gain_db(music, -18.0)))
                self.tracks.append(self._track("audio", [seg], "music"))
            self.warnings.append("music bed placed at plan gain; sidechain ducking is NOT expressible in a draft - "
                                 "the owner adds Auto-ducking in CapCut if wanted")
        elif music.get("attach_in_app") or music.get("trending_sound_id"):
            self.warnings.append(f"music: attach sound {music.get('trending_sound_id')} in-app at posting (license {music.get('license')}); no music track written")
        sfx_tracks: list[list[dict]] = []
        for s in audio.get("sfx") or []:
            sp = ce.resolve_path(s.get("path"), self.base)
            if not (sp and os.path.isfile(sp)):
                self.warnings.append(f"sfx missing: {sp}")
                continue
            pr = ce.probe_media(sp)
            mat = self._audio_material(sp, pr, "sound_effect")
            at = float(s.get("at", 0.0) or 0.0)
            seg = self._audio_segment(mat, 0.0, pr["duration"], us(at, self.fps), ce.db_to_lin(ce.gain_db(s, -12.0)))
            placed_ok = False
            for tr in sfx_tracks:  # first track where it does not overlap
                last = tr[-1]
                if seg["target_timerange"]["start"] >= last["target_timerange"]["start"] + last["target_timerange"]["duration"]:
                    tr.append(seg); placed_ok = True; break
            if not placed_ok:
                sfx_tracks.append([seg])
        for k, tr in enumerate(sfx_tracks):
            self.tracks.append(self._track("audio", tr, "sfx" if k == 0 else f"sfx {k + 1}"))
        # text overlays (hook / callout / end card / text stickers) - never speech captions
        items = ce.layout_overlays(plan, total_duration=capcut_total / US)
        guard = ce.caption_density_guard(items)
        if guard:
            raise ce.PlanError(guard)
        txt_segs = []
        for it in items:
            mat = self._text_material(it)
            seg = self._text_segment(mat, it)
            seg["_plan_overlay"] = it["id"]
            txt_segs.append(seg)
        if txt_segs:
            self.tracks.append(self._track("text", txt_segs))
        # draft_content
        dc = copy.deepcopy(self.tpl)
        dc.update({"id": self.timeline_id, "name": self.name, "duration": capcut_total, "fps": float(self.fps),
                   "create_time": self.now_s, "update_time": self.now_s,
                   "canvas_config": {"ratio": "9:16" if (self.W, self.H) == (1080, 1920) else "original",
                                     "width": self.W, "height": self.H, "background": None},
                   "tracks": self.tracks, "materials": self.materials})
        # strip private markers before saving (kept in the report)
        seg_map = []
        for t in dc["tracks"]:
            for s in t["segments"]:
                seg_map.append({"segment": s["id"], "track": t["type"], "plan_clip": s.pop("_plan_clip", None),
                                "plan_overlay": s.pop("_plan_overlay", None),
                                "start_s": s["target_timerange"]["start"] / US, "duration_s": s["target_timerange"]["duration"] / US})
        return {"draft_content": dc, "duration_us": capcut_total, "segments": seg_map}

    def meta_info(self, fold_path: str, sizes_total: int, duration_us: int) -> dict:
        """draft_meta_info.json: every identity/time field is ours; nothing time-related may leak from the
        template (V2 fix 2026-09-17: tm_duration used to stay at the template's 5133333 us for every draft)."""
        meta = copy.deepcopy(self.tpl_meta)
        entries = [{"ai_group_type": "", "create_time": self.now_s, "duration": 33333, "enter_from": 0, "extra_info": "",
                    "file_Path": "", "height": 0, "id": ce.plain_uuid(), "import_time": self.now_s, "import_time_ms": self.now_us,
                    "item_source": 1, "material_color_tag": "", "md5": "", "metetype": "none",
                    "roughcut_time_range": {"duration": 33333, "start": 0}, "sub_time_range": {"duration": -1, "start": -1},
                    "type": 0, "width": 0}]
        for e in self.meta_media.values():
            e2 = {k: v for k, v in e.items() if not k.startswith("_")}
            entries.append(e2)
        groups = []
        for g in meta.get("draft_materials", []):
            groups.append({"type": g["type"], "value": entries if g["type"] == 0 else []})
        if not groups:
            groups = [{"type": 0, "value": entries}] + [{"type": t, "value": []} for t in (1, 2, 3, 6, 7, 8)]
        meta.update({"draft_materials": groups, "draft_fold_path": fold_path.replace("\\", "/"),
                     "draft_root_path": os.path.abspath(self.drafts_dir).replace("/", "\\"),
                     "draft_id": self.draft_id, "draft_name": self.name, "draft_cover": "draft_cover.jpg",
                     "draft_timeline_materials_size_": int(sizes_total), "tm_draft_create": self.now_us,
                     "tm_draft_modified": self.now_us, "tm_draft_removed": 0, "tm_duration": int(duration_us)})
        return meta, [e["id"] for e in entries]


def validate_draft(draft_dir: str, expected_duration_us: int) -> list[str]:
    errors = []
    dc = ce.load_json(os.path.join(draft_dir, "draft_content.json"))
    meta = ce.load_json(os.path.join(draft_dir, "draft_meta_info.json"))
    ids = set()
    for cat, arr in dc["materials"].items():
        for m in arr:
            if "id" in m:
                ids.add(m["id"])
    end = 0
    for t in dc["tracks"]:
        for s in t["segments"]:
            if s["material_id"] not in ids:
                errors.append(f"segment {s['id']} material {s['material_id']} missing")
            for r in s.get("extra_material_refs") or []:
                if r not in ids:
                    errors.append(f"segment {s['id']} extra ref {r} missing")
            end = max(end, s["target_timerange"]["start"] + s["target_timerange"]["duration"])
            if t["type"] == "audio" and s.get("clip") is not None:
                errors.append(f"audio segment {s['id']} has a clip object (must be null)")
    if dc["duration"] != end:
        errors.append(f"draft duration {dc['duration']} != last segment end {end}")
    if expected_duration_us != end:
        errors.append(f"expected duration {expected_duration_us} != last segment end {end}")
    if meta.get("tm_duration") != end:
        errors.append(f"draft_meta_info tm_duration {meta.get('tm_duration')} != timeline end {end}")
    meta_ids = {e["id"] for g in meta["draft_materials"] if g["type"] == 0 for e in g["value"]}
    for m in dc["materials"]["videos"]:
        if not os.path.isfile(m["path"]):
            errors.append(f"video material path missing: {m['path']}")
        if m.get("local_material_id") not in meta_ids:
            errors.append(f"video material {m['id']} local_material_id not registered in draft_meta_info")
    for m in dc["materials"]["audios"]:
        if not os.path.isfile(m["path"]):
            errors.append(f"audio material path missing: {m['path']}")
    for m in dc["materials"]["texts"]:
        c = json.loads(m["content"])
        n = ce.utf16_len(c["text"])
        for st in c["styles"]:
            if st["range"][1] > n or st["range"][0] < 0:
                errors.append(f"text material {m['id']} style range {st['range']} outside text length {n}")
    return errors


def run_capcut_cli(draft_dir: str, log_path: str) -> dict:
    cli = ce.find_capcut_cli()
    out = {"capcut_cli": cli}
    if not cli:
        out["note"] = "capcut-cli not found (npm install -g capcut-cli@latest)"
        return out
    for cmd_name in ("lint", "version"):
        cp = ce.run(cli + [cmd_name, draft_dir], log_path=log_path)
        txt = (cp.stdout or "").strip()
        try:
            out[cmd_name] = json.loads(txt)
        except Exception:
            out[cmd_name] = {"raw": txt[-4000:], "stderr": (cp.stderr or "")[-2000:]}
        out[f"{cmd_name}_exit"] = cp.returncode
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="edit-plan.json -> CapCut 9.4 draft")
    ap.add_argument("plan")
    ap.add_argument("--name", required=True, help="draft folder / project name (no spaces or colons advised)")
    ap.add_argument("--drafts-dir", default=ce.CAPCUT_DRAFTS_DIR)
    ap.add_argument("--template", default=ce.CAPCUT_TEMPLATE_DIR)
    ap.add_argument("--project-copy", default=None, help="our own copy of the draft (default <plan dir>\\project\\capcut\\<name>)")
    ap.add_argument("--no-register", action="store_true")
    ap.add_argument("--timelines-mirror", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-lint", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        plan, base = ce.load_plan(args.plan)
    except ce.PlanError as e:
        print(f"REFUSED/INVALID: {e}", file=sys.stderr)
        return 3 if "owner rule" in str(e) else 1
    name = args.name.strip()
    if not name or any(ch in name for ch in ':<>"|?*\\/'):
        print("invalid --name (no path separators or : < > \" | ? *)", file=sys.stderr)
        return 1
    drafts_dir = os.path.abspath(args.drafts_dir)
    live = os.path.normcase(drafts_dir) == os.path.normcase(os.path.abspath(ce.CAPCUT_DRAFTS_DIR))
    if live and ce.capcut_running() and not args.force:
        print("CapCut.exe is running: close it before writing into the live draft store (or pass --force).", file=sys.stderr)
        return 4
    if not os.path.isfile(os.path.join(args.template, "draft_content.json")):
        print(f"template draft_content.json missing in {args.template}", file=sys.stderr)
        return 1
    fps = int(plan["project"]["fps"])
    probes = {}
    for c in plan["clips"]:
        p = ce.resolve_path(c["path"], base)
        if not os.path.isfile(p):
            print(f"clip {c['id']}: file not found {p}", file=sys.stderr)
            return 1
        probes[p] = ce.probe_media(p)
    plan_tl = json.loads(json.dumps(plan))
    for c in plan_tl["clips"]:
        c["path"] = ce.resolve_path(c["path"], base)
    placed, total_render = ce.compute_timeline(plan_tl, probes)
    b = DraftBuilder(plan, base, args.template, name, drafts_dir, fps)
    try:
        built = b.build(probes, placed, total_render)
    except ce.PlanError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    draft_dir = os.path.join(drafts_dir, name)
    os.makedirs(draft_dir, exist_ok=True)
    for d in EMPTY_DIRS:
        os.makedirs(os.path.join(draft_dir, d), exist_ok=True)
    fold_path = draft_dir.replace("\\", "/")
    sizes_total = sum(e.get("_size", 0) for e in b.meta_media.values())
    meta, meta_ids = b.meta_info(fold_path, sizes_total, built["duration_us"])
    dc = built["draft_content"]
    ce.save_json(os.path.join(draft_dir, "draft_content.json"), dc, compact=True)
    ce.save_json(os.path.join(draft_dir, "draft_meta_info.json"), meta, compact=True)
    ce.save_json(os.path.join(draft_dir, "draft_virtual_store.json"), {
        "draft_materials": [],
        "draft_virtual_store": [
            {"type": 0, "value": [{"creation_time": 0, "display_name": "", "filter_type": 0, "id": "", "import_time": 0,
                                   "import_time_us": 0, "material_color_tag": "", "sort_sub_type": 0, "sort_type": 0,
                                   "subdraft_filter_type": 0}]},
            {"type": 1, "value": [{"child_id": i, "parent_id": ""} for i in meta_ids]},
            {"type": 2, "value": []}]}, compact=True)
    ce.save_json(os.path.join(draft_dir, "timeline_layout.json"),
                 {"dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [b.timeline_id], "timelineNames": ["Timeline 01"]}],
                  "layoutOrientation": 1}, compact=True)
    ce.write_text(os.path.join(draft_dir, "draft_settings"),
                  f"[General]\ndraft_create_time={b.now_s}\ndraft_last_edit_time={b.now_s}\nreal_edit_seconds=0\nreal_edit_keys=0\n")
    for f in TEMPLATE_FILES_VERBATIM:
        src = os.path.join(args.template, f)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(draft_dir, f))
    if args.timelines_mirror:
        tdir = os.path.join(draft_dir, "Timelines", b.timeline_id)
        os.makedirs(tdir, exist_ok=True)
        ce.save_json(os.path.join(draft_dir, "Timelines", "project.json"),
                     {"main_timeline_id": b.timeline_id, "timelines": [{"id": b.timeline_id, "name": "Timeline 01"}], "version": 0}, compact=True)
        shutil.copyfile(os.path.join(draft_dir, "draft_content.json"), os.path.join(tdir, "draft_content.json"))
    # cover: first frame of the first clip
    log_path = os.path.join(draft_dir, "build.log")
    if os.path.exists(log_path):
        os.remove(log_path)
    try:
        first = placed[0]["clip"]
        fp = ce.resolve_path(first["path"], base)
        ce.run([ce.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{float(first['in']):.3f}", "-i", fp,
                "-frames:v", "1", "-update", "1", "-vf", "scale=540:-2", os.path.join(draft_dir, "draft_cover.jpg")], log_path=log_path)
    except Exception as e:  # cover is cosmetic
        b.warnings.append(f"cover not written: {e}")
    # register in root_meta_info.json
    registered = None
    if not args.no_register:
        root_path = os.path.join(drafts_dir, "root_meta_info.json")
        if os.path.isfile(root_path):
            bak = root_path + ".bak-" + ce.stamp()
            shutil.copyfile(root_path, bak)
            root = ce.load_json(root_path)
        else:
            bak = None
            root = {"all_draft_store": [], "draft_ids": 0, "root_path": drafts_dir.replace("\\", "/")}
        entry = {"cloud_draft_cover": False, "cloud_draft_sync": False, "draft_cloud_last_action_download": False,
                 "draft_cloud_purchase_info": "", "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "",
                 "draft_cloud_videocut_purchase_info": "", "draft_cover": fold_path + "\\draft_cover.jpg",
                 "draft_fold_path": fold_path, "draft_id": b.draft_id, "draft_is_ai_shorts": False,
                 "draft_is_cloud_temp_draft": False, "draft_is_infinite_canvas_draft": False, "draft_is_invisible": False,
                 "draft_is_pippit_draft": False, "draft_is_web_article_video": False,
                 "draft_json_file": fold_path + "\\draft_content.json", "draft_name": name, "draft_new_version": "",
                 "draft_root_path": drafts_dir.replace("/", "\\"), "draft_timeline_materials_size": int(sizes_total),
                 "draft_type": "", "draft_web_article_video_enter_from": "", "pippit_avatar_url": "", "pippit_extra_info": "",
                 "pippit_id": "", "pippit_user_name": "", "streaming_edit_draft_ready": True, "tm_draft_cloud_completed": "",
                 "tm_draft_cloud_entry_id": -1, "tm_draft_cloud_modified": 0, "tm_draft_cloud_parent_entry_id": -1,
                 "tm_draft_cloud_space_id": -1, "tm_draft_cloud_user_id": -1, "tm_draft_create": b.now_us,
                 "tm_draft_modified": b.now_us, "tm_draft_removed": 0, "tm_duration": built["duration_us"]}
        store = [e for e in root.get("all_draft_store", []) if e.get("draft_name") != name and
                 os.path.normcase(e.get("draft_fold_path", "")) != os.path.normcase(fold_path)]
        replaced = len(root.get("all_draft_store", [])) - len(store)
        store.append(entry)
        root["all_draft_store"] = store
        root["draft_ids"] = len(store)
        root.setdefault("root_path", drafts_dir.replace("\\", "/"))
        ce.save_json(root_path, root, compact=True)
        registered = {"root_meta_info": root_path, "backup": bak, "replaced_previous_entry": replaced, "entries_now": len(store)}
    # validate
    errors = validate_draft(draft_dir, built["duration_us"])
    cli = {} if args.no_lint else run_capcut_cli(draft_dir, log_path)
    # our own copy (never touched by CapCut re-saves)
    copy_dir = args.project_copy or os.path.join(os.path.dirname(os.path.abspath(args.plan)), "project", "capcut", name)
    if os.path.normcase(os.path.abspath(copy_dir)) != os.path.normcase(draft_dir):
        if os.path.isdir(copy_dir):
            shutil.rmtree(copy_dir)
        shutil.copytree(draft_dir, copy_dir)
    report = {"draft_dir": draft_dir, "project_copy": copy_dir, "draft_id": b.draft_id, "timeline_id": b.timeline_id,
              "capcut_duration_s": built["duration_us"] / US, "render_duration_s": total_render,
              "note": "CapCut keeps segments contiguous: draft duration = sum of pieces; the ffmpeg render overlaps "
                      "transitions so final.mp4 is shorter by the sum of transition durations",
              "tracks": [{"type": t["type"], "name": t.get("name", ""), "segments": len(t["segments"])} for t in dc["tracks"]],
              "materials": {k: len(v) for k, v in dc["materials"].items() if v},
              "media": [{"path": e["file_Path"], "metetype": e["metetype"], "duration_s": e["duration"] / US} for e in b.meta_media.values()],
              "segments": built["segments"], "registered": registered, "timelines_mirror": bool(args.timelines_mirror),
              "validation_errors": errors, "warnings": b.warnings, "capcut_cli": cli, "generated": ce.now_iso(),
              "open_in_capcut": "start CapCut (restart it if it was open) -> the draft is listed by name; on first open CapCut "
                                "re-saves the folder (adds .bak/template-2.tmp, snaps durations to the frame grid) - expected."}
    ce.save_json(os.path.join(draft_dir, "build-report.json"), report)
    if cli:
        ce.save_json(os.path.join(draft_dir, "lint.json"), cli)
    if os.path.normcase(os.path.abspath(copy_dir)) != os.path.normcase(draft_dir):
        shutil.copyfile(os.path.join(draft_dir, "build-report.json"), os.path.join(copy_dir, "build-report.json"))
        if cli:
            shutil.copyfile(os.path.join(draft_dir, "lint.json"), os.path.join(copy_dir, "lint.json"))
    ce.history_line(os.path.dirname(os.path.abspath(args.plan)), f"capcut draft built: {draft_dir} ({built['duration_us'] / US:.2f}s, "
                    f"{len(errors)} validation errors, lint exit {cli.get('lint_exit')})")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        lint = cli.get("lint", {})
        summ = lint.get("summary") if isinstance(lint, dict) else None
        print(json.dumps({"draft_dir": draft_dir, "project_copy": copy_dir, "capcut_duration_s": report["capcut_duration_s"],
                          "render_duration_s": total_render, "tracks": report["tracks"], "validation_errors": errors,
                          "lint_summary": summ, "lint_exit": cli.get("lint_exit"), "warnings": b.warnings,
                          "registered": registered}, ensure_ascii=False))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
