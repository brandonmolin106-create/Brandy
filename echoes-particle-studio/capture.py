"""Face performance capture with MediaPipe FaceLandmarker.

usage: python capture.py VIDEO OUT.npz [--stride N] [--image-mode]

Stores per processed frame: 478 landmarks (x, y in pixels, z in pixel
units), 52 blendshape scores, the 4x4 facial transformation matrix, and
a validity flag. Dark / low-contrast frames are CLAHE-boosted for the
detector only.
"""
import argparse
import subprocess
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

MODEL = '/opt/models/face_landmarker.task'


def probe(video):
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height,avg_frame_rate', '-of', 'csv=p=0', video]).decode().strip().split(',')
    w, h = int(out[0]), int(out[1])
    num, den = out[2].split('/')
    return w, h, float(num) / float(den)


def frames(video, w, h):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', video, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE, bufsize=w * h * 3 * 4)
    n = w * h * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    p.wait()


def boost(rgb, clahe):
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    lab[..., 0] = clahe.apply(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('out')
    ap.add_argument('--stride', type=int, default=1)
    ap.add_argument('--image-mode', action='store_true')
    a = ap.parse_args()

    w, h, fps = probe(a.video)
    mode = vision.RunningMode.IMAGE if a.image_mode else vision.RunningMode.VIDEO
    opts = vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=MODEL), running_mode=mode,
        output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1,
        min_face_detection_confidence=0.25, min_face_presence_confidence=0.25, min_tracking_confidence=0.25)
    det = vision.FaceLandmarker.create_from_options(opts)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    L, B, M, V, T, S = [], [], [], [], [], []
    bs_names = None
    for i, rgb in enumerate(frames(a.video, w, h)):
        if i % a.stride:
            continue
        img = boost(rgb, clahe)
        mi = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img))
        if a.image_mode:
            res = det.detect(mi)
        else:
            res = det.detect_for_video(mi, int(round(i * 1000.0 / fps)))
        T.append(i / fps)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        if res.face_landmarks:
            lm = np.array([[p.x * w, p.y * h, p.z * w] for p in res.face_landmarks[0]], np.float32)
            bs = np.array([c.score for c in res.face_blendshapes[0]], np.float32)
            if bs_names is None:
                bs_names = [c.category_name for c in res.face_blendshapes[0]]
            mat = np.array(res.facial_transformation_matrixes[0], np.float32).reshape(4, 4)
            x0, y0 = np.clip(lm[:, :2].min(0).astype(int), 0, [w - 1, h - 1])
            x1, y1 = np.clip(lm[:, :2].max(0).astype(int), 1, [w, h])
            crop = gray[y0:y1, x0:x1]
            sharp = float(cv2.Laplacian(crop, cv2.CV_32F).var()) if crop.size > 64 else 0.0
            L.append(lm); B.append(bs); M.append(mat); V.append(True); S.append(sharp)
        else:
            L.append(np.full((478, 3), np.nan, np.float32)); B.append(np.full(52, np.nan, np.float32))
            M.append(np.full((4, 4), np.nan, np.float32)); V.append(False); S.append(0.0)
        if len(T) % 500 == 0:
            print(f'{len(T)} frames, valid {np.mean(V):.3f}', flush=True)

    np.savez_compressed(a.out, lm=np.array(L), bs=np.array(B), mat=np.array(M), valid=np.array(V),
                        t=np.array(T), sharp=np.array(S), fps=fps, w=w, h=h, stride=a.stride,
                        bs_names=np.array(bs_names or []))
    print('done', len(T), 'frames, valid', float(np.mean(V)), file=sys.stderr)


if __name__ == '__main__':
    main()
