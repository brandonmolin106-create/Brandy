"""Cut the picture to the narration for "0922 narration-match".

Needs out/timeline.json + out/full_mix.wav from build_audio.py. Steps:
  1. every shot in edl.SHOTS is trimmed frame-exact from its source clip
     (slow-motion shots are frame-blended), scaled to 1920x1080 @ 24 fps
  2. shots are joined with their transitions (xfade) in groups, then the
     groups are joined the same way
  3. finishing pass: shake + flash on impacts, RGB glitch accents, grade,
     bloom, gold glow on the reveal moments, grain, vignette, 2.39:1 bars
  4. the mastered mix is laid under it -> out/endless_destiny_narration_match.mp4
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import edl

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
TMP = ROOT / "work" / "render"
FPS = 24
W, H = 1920, 1080
BAR = 138  # 2.39:1 letterbox inside 1920x1080
GROUP = 12


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(map(str, cmd))}\n{r.stderr[-3000:]}")


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout)


def cached(name, *key):
    """Render cache: a file name that changes whenever its inputs change."""
    h = hashlib.sha1(repr(key).encode()).hexdigest()[:10]
    return TMP / f"{name}_{h}.mp4"


def F(t):
    return int(round(t * FPS))


def resolve_shots(tl):
    lines, chunk_starts = tl["lines"], tl["chunk_starts"]
    shots = []
    for anchor, off, clip, src_in, tr, tdur, opts in edl.SHOTS:
        if anchor == "t0":
            cut = 0.0
        elif isinstance(anchor, int):
            cut = lines[anchor]["start"] + off
        elif anchor[0] == "c":
            cut = chunk_starts[str(anchor[1])] + off
        elif anchor[0] == "e":
            cut = lines[anchor[1]]["end"] + off
        shots.append(dict(cut=cut, clip=clip, src_in=src_in, tr=tr or "fade",
                          tf=0 if tr is None else max(2, F(tdur)), speed=opts.get("speed", 1.0)))
    total = F(tl["duration"])
    for i, s in enumerate(shots):
        s["start"] = 0 if i == 0 else F(s["cut"]) - s["tf"] // 2
    for i, s in enumerate(shots):
        nxt = shots[i + 1] if i + 1 < len(shots) else None
        s["end"] = nxt["start"] + nxt["tf"] if nxt else total
        s["frames"] = s["end"] - s["start"]
        assert s["frames"] > 0, f"shot {i} has no length"
        if nxt:
            assert nxt["start"] >= s["start"] + s["tf"], f"shots {i}/{i + 1} overlap their transitions"
    return shots


def clip_path(clip):
    return ROOT / "work/clips" / f"{edl.CLIPS[clip]}.mp4"


def render_shot(i, s, durations, problems):
    n = s["frames"]
    out = cached(f"shot_{i:03d}", s["clip"], s["src_in"], s["cut"], s["start"], n, s["speed"])
    if out.exists():
        return out
    if s["clip"] == "BLACK":
        run(["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}",
             "-frames:v", str(n), "-c:v", "libx264", "-crf", "12", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", str(out)])
        return out
    src = clip_path(s["clip"])
    dur = durations[s["clip"]]
    sp = s["speed"]
    ss = s["src_in"] + (s["start"] / FPS - s["cut"]) * sp
    need = n / FPS * sp
    if ss < 0 or ss + need > dur + 0.02:
        problems.append(f"shot {i} ({s['clip']} @ {s['src_in']}): needs {ss:.2f}-{ss + need:.2f}s of a {dur:.2f}s clip")
        ss = min(max(ss, 0), max(dur - need, 0))
    vf = ["setpts=PTS-STARTPTS"]
    if sp != 1.0:
        vf += [f"setpts=PTS/{sp}", f"framerate=fps={FPS}:scene=100"]
    vf += [f"fps={FPS}", f"scale={W}:{H}:flags=lanczos", "setsar=1"]
    if "C05" <= s["clip"] <= "C16":  # the 720p renders
        vf.append("unsharp=5:5:0.45:5:5:0")
    vf += ["format=yuv420p", "tpad=stop_mode=clone:stop_duration=3"]
    run(["ffmpeg", "-nostdin", "-y", "-ss", f"{ss:.3f}", "-i", str(src), "-an", "-vf", ",".join(vf),
         "-frames:v", str(n), "-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-r", str(FPS), str(out)])
    return out


def chain(items, out):
    """items: [(path, frames, transition, transition_frames)] -> joined file."""
    if len(items) == 1:
        return items[0][0], items[0][1]
    out = cached(out, [(str(p), n, tr, tf) for p, n, tr, tf in items])
    acc = items[0][1] + sum(n - tf for _, n, _, tf in items[1:])
    if out.exists():
        return out, acc
    cmd = ["ffmpeg", "-nostdin", "-y"]
    for p, *_ in items:
        cmd += ["-i", str(p)]
    parts, acc, prev = [], items[0][1], "[0:v]"
    for k in range(len(items)):
        parts.append(f"[{k}:v]settb=AVTB,fps={FPS}[i{k}]")
    prev = "[i0]"
    for k in range(1, len(items)):
        _, frames, tr, tf = items[k]
        off = (acc - tf) / FPS
        parts.append(f"{prev}[i{k}]xfade=transition={tr}:duration={tf / FPS:.4f}:offset={off:.4f}[x{k}]")
        prev = f"[x{k}]"
        acc += frames - tf
    cmd += ["-filter_complex", ";".join(parts), "-map", prev, "-frames:v", str(acc),
            "-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)]
    run(cmd)
    return out, acc


def finishing_filter(tl):
    cues = tl["cues"]
    impacts = [c["t"] for c in cues if c["kind"] == "impact"]
    booms = [c["t"] for c in cues if c["kind"] in ("softboom", "rumble")]
    glitches = [c["t"] for c in cues if c["kind"] == "glitch"]
    glows = [c["t"] for c in cues if c["kind"] == "glow"]

    # max(t-T,0) keeps exp() from overflowing to inf before a cue (inf*0 = NaN = black frame)
    def decay(times, amp, rate, dur):
        return "+".join(f"{amp}*exp(-max(t-{t:.3f},0)*{rate})*between(t,{t:.3f},{t + dur:.3f})" for t in times) or "0"

    def wobble(hits, freq, phase):
        return "+".join(f"{a:.2f}*exp(-max(t-{t:.3f},0)*5)*sin(max(t-{t:.3f},0)*{freq}+{phase})"
                        f"*between(t,{t:.3f},{t + 1.2:.3f})" for t, a in hits) or "0"

    shake = [(t, 14) for t in impacts] + [(t, 6) for t in booms]
    sx, sy = wobble(shake, 67, 0), wobble([(t, a * 0.6) for t, a in shake], 53, 1)
    cw, ch = W - 48, H - 27
    flash = decay(impacts, 0.22, 7, 0.8)
    glitch_on = "+".join(f"between(t,{t:.3f},{t + 0.35:.3f})" for t in glitches) or "0"

    f = []
    f.append(f"[0:v]crop=w={cw}:h={ch}:x='24+({sx})':y='13+({sy})',scale={W}:{H}:flags=bicubic,"
             f"eq=brightness='{flash}':eval=frame,"
             f"rgbashift=rh=9:bh=-9:gv=3:enable='{glitch_on}',"
             "colorbalance=rs=-0.03:bs=0.05:rm=0.01:bm=0.0:rh=0.05:gh=0.02:bh=-0.04,"
             "curves=master='0/0 0.1/0.07 0.5/0.52 0.88/0.93 1/1',eq=saturation=1.06,format=gbrp[g]")
    f.append(f"[g]split={2 + len(glows)}[base][b]" + "".join(f"[s{k}]" for k in range(len(glows))))
    f.append(f"[b]scale=480:270,gblur=sigma=9,scale={W}:{H}[bl]")
    f.append("[base][bl]blend=all_mode=screen:all_opacity=0.28[bloom]")
    last = "[bloom]"
    for k, t in enumerate(glows):
        # full-length branch that is transparent outside its window, so the
        # overlay never has to buffer frames while it waits
        d = 4.0
        f.append(f"[s{k}]scale=480:270,gblur=sigma=16,scale={W}:{H},"
                 f"colorchannelmixer=rr=1.25:gg=0.95:bb=0.55,format=rgba,colorchannelmixer=aa=0.55,"
                 f"fade=t=in:st={t:.3f}:d=1.0:alpha=1,fade=t=out:st={t + d - 1.8:.3f}:d=1.8:alpha=1[gl{k}]")
        f.append(f"{last}[gl{k}]overlay=format=gbrp[o{k}]")
        last = f"[o{k}]"
    f.append(f"{last}format=yuv420p,noise=c0s=5:c0f=t+u,vignette=angle=PI/4.6,"
             f"drawbox=x=0:y=0:w=iw:h={BAR}:color=black:t=fill,"
             f"drawbox=x=0:y=ih-{BAR}:w=iw:h={BAR}:color=black:t=fill,format=yuv420p[v]")
    return ";".join(f)


def main(preview=None):
    tl = json.load(open(OUT / "timeline.json"))
    TMP.mkdir(parents=True, exist_ok=True)
    shots = resolve_shots(tl)
    durations = {c: probe_duration(clip_path(c)) for c in edl.CLIPS}
    problems = []
    rendered = []
    for i, s in enumerate(shots):
        rendered.append((render_shot(i, s, durations, problems), s["frames"], s["tr"], s["tf"]))
        print(f"\rshots {i + 1}/{len(shots)}", end="", flush=True)
    print()
    for p in problems:
        print("WARNING:", p)
    groups = []
    for g in range(0, len(rendered), GROUP):
        items = rendered[g:g + GROUP]
        path, frames = chain(items, f"group_{g // GROUP:02d}")
        groups.append((path, frames, items[0][2], items[0][3]))
        print(f"group {g // GROUP} -> {frames} frames")
    edit, frames = chain(groups, "edit")
    assert frames == F(tl["duration"]), f"edit is {frames} frames, timeline is {F(tl['duration'])}"

    final = OUT / "endless_destiny_narration_match.mp4"
    cmd = ["ffmpeg", "-nostdin", "-y", "-i", str(edit), "-i", str(OUT / "full_mix.wav"),
           "-filter_complex", finishing_filter(tl), "-map", "[v]", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-tune", "film", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "-shortest"]
    if preview:  # first N seconds only, to check the finishing pass
        cmd += ["-t", str(preview)]
        final = OUT / f"preview_{int(preview)}s.mp4"
    run(cmd + [str(final)])
    print("wrote", final)


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else None)
