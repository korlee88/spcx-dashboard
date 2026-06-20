"""data/bgm.mp3 생성기 (원본·로열티프리/CC0).

외부 CC0 음원 사이트(FreePD=JS 렌더링, archive.org=CC0 검색 불가)가 빌드 환경에서
안정적으로 접근되지 않아, 저작권·네트워크 의존이 전혀 없는 '원본' 배경 음악을 직접 합성한다.
구성: 따뜻한 메이저7 패드(C–Am–F–G) + 부드러운 아르페지오 + 약한 잔향 → 나레이션 아래 10%용.

v2: 단일 사인파 패드가 어택 이후 ~3.5초간 완전히 평탄해 "밋밋하다"는 피드백을 받음 — 디튠
유니즌(2voice 비트), 서브베이스 펄스, 느린 밝기 LFO, 사이클별 아르페지오 패턴 변주로 정적인
구간을 없애 끊임없이 미세하게 움직이도록 개선(전체 톤·길이·믹스 밸런스는 유지).
재생성: python scripts/make_bgm.py  (출력: data/bgm.mp3, 이음매 없는 ~63초 루프)
"""
import math
from pathlib import Path
import numpy as np

SR = 44100
CHORD_SEC = 4.0
CYCLES = 4
FADE = 1.0          # 루프 이음매 크로스페이드 길이(초)
ARP_NOTE = 0.5      # 아르페지오 한 음 길이(초)
DETUNE_CENTS = 5.0  # 유니즌 디튠 폭(센트) — 두 보이스가 살짝 어긋나며 천천히 비트(beat)쳐 움직임을 만든다

# 코드별 음정(Hz): Cmaj7 – Am7 – Fmaj7 – G7  + 서브베이스(루트 한 옥타브 아래)
CHORDS = [
    ([261.63, 329.63, 392.00, 493.88], 130.81),  # Cmaj7
    ([220.00, 261.63, 329.63, 392.00], 110.00),   # Am7
    ([174.61, 220.00, 261.63, 329.63],  87.31),   # Fmaj7
    ([196.00, 246.94, 293.66, 349.23],  98.00),   # G7
]
# 코드당 아르페지오 패턴(코드 톤 인덱스, 한 옥타브 위로 연주) — 사이클마다 살짝 변주해 4회 반복이 기계적으로 들리지 않게 함
ARP_PATTERNS = [
    [0, 1, 2, 3, 2, 1, 2, 3],
    [0, 2, 1, 3, 2, 3, 1, 2],
    [0, 1, 2, 3, 2, 1, 2, 3],
    [2, 1, 0, 1, 2, 3, 2, 1],
]


def _detune_ratio(cents):
    return 2 ** (cents / 1200)


def _tone(freq, n, harm):
    t = np.arange(n) / SR
    w = np.sin(2 * np.pi * freq * t)
    for k, amp in harm:
        w += amp * np.sin(2 * np.pi * k * freq * t)
    return w


def grain(freqs, sub, dur, bright_lfo):
    """패드 코드 — 디튠 유니즌(2voice) 상부음 + 펄싱 서브베이스.

    bright_lfo: 길이 n(≈dur*SR) 배열(0~1) — 고배음 비중을 느리게 흔들어 음색이
    계속 미세하게 밝아지고 어두워지게 한다(긴 사이드체인-필터 스윕 느낌).
    """
    n = int(dur * SR)
    if len(bright_lfo) < n:
        lfo = np.pad(bright_lfo, (0, n - len(bright_lfo)), mode="edge")
    else:
        lfo = bright_lfo[:n]
    t = np.arange(n) / SR

    # ── 상부 코드톤: 살짝 어긋난 2voice가 천천히 비트치며 정적인 느낌을 없앤다 ──
    upper = np.zeros(n)
    for f in freqs:
        for cents in (-DETUNE_CENTS, DETUNE_CENTS):
            fd = f * _detune_ratio(cents)
            upper += 0.5 * _tone(fd, n, [(2, 0.22 + 0.10 * lfo), (3, 0.08 + 0.06 * lfo)])

    # ── 서브베이스: 코드마다 두 번 살짝 부풀어 오르는 펄스 — 맥동하는 리듬감 ──
    pulse = 1.0 + 0.35 * (
        np.exp(-((t - 0.15 * dur) / 0.18) ** 2) +
        np.exp(-((t - 0.62 * dur) / 0.18) ** 2)
    )
    bass = 1.1 * _tone(sub, n, [(2, 0.25)]) * pulse

    sig = upper + bass
    env = np.ones(n)
    a, r = int(0.5 * SR), int(1.6 * SR)
    env[:a] = np.linspace(0, 1, a) ** 2
    env[-r:] = np.linspace(1, 0, r) ** 2
    # 서스테인 구간에도 느린 스웰을 줘 완전히 평탄한 구간이 없게 한다
    swell = 1.0 + 0.06 * np.sin(2 * np.pi * 0.18 * t)
    return sig * env * swell


def pluck(freq, n):
    """뜯는 듯한 짧은 음(아르페지오용) — 빠른 어택 + 지수 감쇠. 살짝 디튠한 2voice로 미세한 셰이머."""
    t = np.arange(n) / SR
    env = np.exp(-t * 4.5)
    w = np.zeros(n)
    for cents in (-3.0, 3.0):
        fd = freq * _detune_ratio(cents)
        w += 0.5 * _tone(fd, n, [(2, 0.4), (3, 0.15)])
    w *= env
    a = int(0.006 * SR)
    w[:a] *= np.linspace(0, 1, a)
    return w


def echo(sig, delay_s=0.36, decay=0.33, taps=3):
    """가벼운 잔향 — 감쇠하는 지연 복사본 몇 개."""
    out = sig.copy()
    d = int(delay_s * SR)
    for i in range(1, taps + 1):
        if i * d < len(sig):
            out[i * d:] += sig[:len(sig) - i * d] * (decay ** i)
    return out


total = int(CHORD_SEC * len(CHORDS) * CYCLES * SR)
buf_len = total + int(2.0 * SR)
pad = np.zeros(buf_len)
arp = np.zeros(buf_len)

# 전체 길이에 걸친 느린 밝기 LFO(0~1) — 코드 경계와 무관하게 연속적으로 흘러야 끊김이 없다
_t_full = np.arange(buf_len) / SR
bright_full = 0.5 + 0.5 * np.sin(2 * np.pi * 0.045 * _t_full)

step = int(CHORD_SEC * SR)
nlen = int(ARP_NOTE * SR)
idx = 0
for c in range(CYCLES):
    arp_pattern = ARP_PATTERNS[c % len(ARP_PATTERNS)]
    for freqs, sub in CHORDS:
        # 패드(다음 코드와 1.6초 겹침)
        g_dur = CHORD_SEC + 1.6
        g_len = int(g_dur * SR)
        g = grain(freqs, sub, g_dur, bright_full[idx:idx + g_len])
        end = min(idx + len(g), buf_len)
        pad[idx:end] += g[:end - idx]
        # 아르페지오 (코드 톤, 한 옥타브 위)
        for k, pi in enumerate(arp_pattern):
            f = freqs[pi % len(freqs)] * 2.0
            s = idx + int(k * ARP_NOTE * SR)
            p = pluck(f, nlen)
            e = min(s + len(p), buf_len)
            arp[s:e] += p[:e - s]
        idx += step

arp = echo(arp)
buf = 0.85 * pad[:total] + 0.5 * arp[:total]

# 이음매 없는 루프: 앞 FADE초를 끝 FADE초와 크로스페이드
F = int(FADE * SR)
head, tail = buf[:F].copy(), buf[-F:].copy()
ramp = np.linspace(0, 1, F)
buf[:F] = head * ramp + tail * (1 - ramp)
loop = buf[:len(buf) - F]

# 정규화 (-3 dBFS)
peak = np.max(np.abs(loop)) or 1.0
loop = loop / peak * (10 ** (-3 / 20))
pcm = (loop * 32767).astype(np.int16)

out = Path(__file__).parent.parent / "data" / "bgm.mp3"
out.parent.mkdir(parents=True, exist_ok=True)
try:
    import lameenc
    enc = lameenc.Encoder()
    enc.set_bit_rate(160)
    enc.set_in_sample_rate(SR)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3 = enc.encode(pcm.tobytes()) + enc.flush()
    out.write_bytes(mp3)
    print(f"✅ {out} ({len(mp3)} bytes, {len(loop) / SR:.1f}s, peak={peak:.2f})")
except ImportError:
    import wave
    wav = out.with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"⚠ lameenc 없음 → {wav} (WAV) 생성. ffmpeg로 mp3 변환 필요")
