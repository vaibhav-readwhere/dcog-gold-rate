"""
Animated Gold Rates Reel — 1080×1920 @ 24 fps
Structure:
  0.0 – 2.6   INTRO    : logo fades-in centre (large) → slides to corner (small)
  2.6 – 14.5  CONTENT  : title + rates appear, hold ~5s so viewers can read
  14.5 – 18.0 OUTRO    : content fades, logo flies back to centre + URL
"""
import math, os
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import moviepy.editor as mpy
except ImportError:
    raise ImportError("pip install moviepy")

# ── Video ─────────────────────────────────────────────────────────────────────
VIDEO_W  = 1080
VIDEO_H  = 1920
FPS      = 24
DURATION = 18.0

# ── Instagram safe zone ───────────────────────────────────────────────────────
SAFE_T, SAFE_B, SAFE_L, SAFE_R = 170, 1530, 95, 875

# ── Palette ───────────────────────────────────────────────────────────────────
GOLD        = (218, 165,  18)
GOLD_BRIGHT = (255, 215,  60)
GOLD_DIM    = (175, 138,  38)
WHITE       = (255, 255, 255)

# ── Asset paths ───────────────────────────────────────────────────────────────
_A   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
_F   = os.path.join(_A, 'fonts')
OFT  = os.path.join(_F, 'Outfit-Variable.ttf')
ABD  = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
ARG  = '/System/Library/Fonts/Supplemental/Arial.ttf'
W_REG, W_SB, W_BOLD, W_EB = 400, 600, 700, 800

# Fonts that support ▲ ▼ — glyphs — bold variants first (macOS → Linux)
_ARROW_FONT_PATHS = [
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',              # macOS bold
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',           # macOS
    '/System/Library/Fonts/Supplemental/Arial.ttf',                   # macOS fallback
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',           # Ubuntu bold
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',                # Ubuntu
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
]
_ARROW_FC: dict = {}

def _arrow_font(sz: int) -> ImageFont.FreeTypeFont:
    if sz in _ARROW_FC: return _ARROW_FC[sz]
    for p in _ARROW_FONT_PATHS:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, sz)
                _ARROW_FC[sz] = f
                return f
            except Exception:
                continue
    _ARROW_FC[sz] = ImageFont.load_default()
    return _ARROW_FC[sz]

# ── Layout ────────────────────────────────────────────────────────────────────
LOGO_Y        = SAFE_T
LOGO_CORNER_H = 200          # full uncropped canvas height in corner
LOGO_INTRO_H  = 400          # full uncropped canvas height for intro / outro
LOGO_MAX_W    = 700          # max width

OFFICIAL_BADGE_H = 36                      # height of OFFICIAL pill beneath logo
TITLE_Y  = LOGO_Y + LOGO_CORNER_H + OFFICIAL_BADGE_H + 22    # ≈ 428
SUBT_Y   = TITLE_Y + 82   # space below title (top padding for subtitle)
DATE_Y   = SUBT_Y  + 62   # space below subtitle (bottom padding)
CARD_Y   = DATE_Y  + 52
ROW_H    = 132
ROWS     = ['24K', '22K', '21K', '18K', '14K']
CARD_H   = len(ROWS) * ROW_H + 50         # 770
CARD_B   = CARD_Y + CARD_H
TAG_Y    = CARD_B + 28

# ── Timeline (seconds) ───────────────────────────────────────────────────────
_BG_IN       = (0.0,  0.9)
_LOGO_FADE   = (0.3,  1.5)   # logo fades in at centre
_LOGO_MOVE   = (1.5,  2.7)   # logo moves to corner
_TITLE       = (2.7,  3.3)
_SUB         = (3.1,  3.6)
_DATE        = (3.2,  3.7)
_CARD        = (3.5,  3.9)
_ROW_BASE    = 3.8
_ROW_GAP     = 0.52           # seconds between rows
_ROW_DUR     = 0.40
_TAG         = (_ROW_BASE + len(ROWS)*_ROW_GAP + 0.1,
                _ROW_BASE + len(ROWS)*_ROW_GAP + 0.7)
_FADE_OUT    = (14.5, 15.5)   # content fades out  (~5s hold after last row)
_OUTRO_LOGO  = (15.2, 16.8)   # logo returns centre
_URL         = (16.0, 17.5)   # website url


# ── Font ──────────────────────────────────────────────────────────────────────
_FC: Dict[Tuple, ImageFont.FreeTypeFont] = {}

def _font(sz: int, w: int = W_REG) -> ImageFont.FreeTypeFont:
    k = (sz, w)
    if k in _FC: return _FC[k]
    if os.path.exists(OFT):
        try:
            f = ImageFont.truetype(OFT, sz)
            if w != W_REG: f.set_variation_by_axes([w])
            _FC[k] = f; return f
        except Exception: pass
    try:
        _FC[k] = ImageFont.truetype(ABD if w >= W_SB else ARG, sz)
    except Exception:
        _FC[k] = ImageFont.load_default()
    return _FC[k]

def _tw(txt, f): bb = f.getbbox(txt); return bb[2]-bb[0]

def _fit(txt, mw, sz, w=W_REG):
    while sz >= 20:
        f = _font(sz, w)
        if _tw(txt, f) <= mw: return f
        sz -= 2
    return _font(20, w)


# ── Easing ────────────────────────────────────────────────────────────────────
_eo  = lambda x: 1-(1-x)**3
_eio = lambda x: .5-.5*math.cos(math.pi*x)

def _p(s, e, t):
    if t<=s: return 0.
    if t>=e: return 1.
    return _eo((t-s)/(e-s))

def _pio(s, e, t):
    if t<=s: return 0.
    if t>=e: return 1.
    return _eio((t-s)/(e-s))


# ── Pre-loaded state (shared across frames) ───────────────────────────────────
class _State:
    def __init__(self, bg_index: int = -1):
        """
        bg_index: which background video to use (0-based).
                  -1 (default) = rotate automatically by day-of-year.
        """
        self._bg_index = bg_index
        self._tex()
        self._logo()

    # ── background (video → static texture → gradient fallback) ────────────
    def _tex(self):
        # Priority 1: background videos — rotate daily
        # Naming: dubai-background-video.mp4, dubai-background-video-2.mp4, …
        # Add more files with the same prefix and they are picked up automatically.
        import glob as _glob
        vids = sorted(_glob.glob(os.path.join(_A, 'dubai-background-video*.mp4')))
        if vids:
            # Use ordinal day so the same video runs all day and rotates each morning.
            # bg_index override lets callers force a specific video (e.g. sample generation).
            if self._bg_index >= 0:
                idx = self._bg_index % len(vids)
            else:
                idx = datetime.today().toordinal() % len(vids)
            vid_path = vids[idx]
            self.vid   = mpy.VideoFileClip(vid_path)
            self.has_v = True
            self.has_t = False
            self.tex   = None
            print(f"[bg] {os.path.basename(vid_path)}  "
                  f"(video {idx+1}/{len(vids)})  "
                  f"({self.vid.duration:.1f}s  {self.vid.size[0]}×{self.vid.size[1]})")
            return

        # Priority 2: static gold texture (panning)
        self.has_v = False
        self.vid   = None
        for n in ('bg_gold.jpg','bg_gold.png','background.jpg','background.png'):
            p = os.path.join(_A, n)
            if not os.path.exists(p): continue
            tw, th = int(VIDEO_W*1.38), int(VIDEO_H*1.38)
            img = Image.open(p).convert('RGB').resize((tw,th), Image.LANCZOS)
            self.tex   = np.array(img, dtype=np.float32)
            self.px    = tw - VIDEO_W
            self.py    = th - VIDEO_H
            self.has_t = True
            print(f"[bg] {n}  ({tw}×{th})")
            return

        # Priority 3: gradient
        self.has_t = False; self.tex = None
        print("[bg] no texture — using gradient")

    # ── logo ────────────────────────────────────────────────────────────────
    def _logo(self):
        # Use logo exactly as-is — no pixel manipulation of any kind.
        for n in ('logo-dark-2.png', 'logo-dark.png', 'logo.png', 'logo.jpg'):
            p = os.path.join(_A, n)
            if not os.path.exists(p): continue
            self.logo = Image.open(p).convert('RGBA')
            print(f"[logo] {n}  {self.logo.size}")
            return
        self.logo = None; print("[logo] none found")

    # ── background array for time t ─────────────────────────────────────────
    def bg(self, t: float) -> np.ndarray:
        H, W = VIDEO_H, VIDEO_W
        fi   = _p(*_BG_IN, t)
        norm = t / DURATION

        if self.has_v:
            # ── Video background ─────────────────────────────────────────────
            # Slow-motion remap: stretch 11.5s source to fill 13.0s output
            vt = min(t * (self.vid.duration / DURATION),
                     self.vid.duration - 0.04)
            c  = self.vid.get_frame(vt).astype(np.float32)   # (H, W, 3)

            # ── Translucent dark base layer (keeps video visible) ───────────
            c *= 0.55

            # ── Top gradient: extra darkness behind text area (top 70%) ──────
            yi    = np.linspace(0, 1, H, dtype=np.float32)
            tgrad = np.clip(1.0 - yi / 0.70, 0, 1) * 0.35
            c    *= (1 - tgrad[:, None, None])

            # ── Bottom gradient: dark strip behind tagline / URL ─────────────
            bgrad = np.clip((yi - 0.80) / 0.20, 0, 1) * 0.25
            c    *= (1 - bgrad[:, None, None])


        elif self.has_t:
            # ── Static texture (panning) ─────────────────────────────────────
            px = int(norm * self.px * 0.65)
            py = int(norm * self.py * 0.35)
            c  = self.tex[py:py+H, px:px+W].copy()
            c *= 0.40
            yi    = np.linspace(0, 1, H, dtype=np.float32)
            extra = np.clip(1 - yi / 0.45, 0, 1) * 0.30
            c    *= (1 - extra[:, None, None])

        else:
            # ── Navy gradient fallback ────────────────────────────────────────
            yi = np.linspace(0,1,H,dtype=np.float32)
            r  = 8+5*yi; g = 11+6*yi; b = 22+11*yi
            c  = np.stack([np.broadcast_to(r[:,None],(H,W)),
                           np.broadcast_to(g[:,None],(H,W)),
                           np.broadcast_to(b[:,None],(H,W))], 2).copy()
            gx,gy = W*.5,H*.90
            xi    = np.arange(W,dtype=np.float32)[None,:]
            yy    = np.arange(H,dtype=np.float32)[:,None]
            dist  = np.sqrt(((xi-gx)/(W*.52))**2+((yy-gy)/(H*.26))**2)
            gl    = np.clip(1.25-dist,0,1)**2.5
            c[:,:,0] = np.clip(c[:,:,0]+gl*95,0,255)
            c[:,:,1] = np.clip(c[:,:,1]+gl*52,0,255)
            c[:,:,2] = np.clip(c[:,:,2]+gl* 3,0,255)

        # ── Vignette (all paths) ─────────────────────────────────────────────
        xi  = np.arange(W, dtype=np.float32)[None,:] / (W-1)
        yi2 = np.arange(H, dtype=np.float32)[:,None] / (H-1)
        v   = np.clip(((xi-.5)*2)**2 + ((yi2-.5)*2)**2, 0, 1) * 0.20
        c  *= (1 - v[:,:,None])

        return np.clip(c * fi, 0, 255).astype(np.uint8)

    # ── logo at target height, alpha ────────────────────────────────────────
    def logo_img(self, h: int, alpha: float = 1.0) -> Optional[Image.Image]:
        if self.logo is None or alpha <= 0: return None
        lw,lh = self.logo.size
        nw,nh = int(lw*h/lh), h
        # Cap width so landscape logos don't overflow the frame
        if nw > LOGO_MAX_W:
            nw = LOGO_MAX_W
            nh = int(lh * nw / lw)
        out   = self.logo.resize((nw,nh), Image.LANCZOS)
        arr   = np.array(out, dtype=np.float32)
        arr[:,:,3] = np.clip(arr[:,:,3]*alpha, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))


# ── helpers ───────────────────────────────────────────────────────────────────
def _draw_official_badge(img: Image.Image, x: int, y: int, alpha: int,
                         logo_w: int = 0) -> Image.Image:
    """Draw 'OFFICIAL GOLD RATE' pill — width matches the logo above."""
    if alpha <= 0: return img
    f   = _font(20, W_BOLD)
    txt = "OFFICIAL GOLD RATE"
    tw  = _tw(txt, f)
    bh  = OFFICIAL_BADGE_H
    # Match badge width to the logo rendered width; fall back to text+padding
    bw  = logo_w if logo_w > tw + 36 else tw + 36
    def _draw(d):
        d.rounded_rectangle([x, y, x+bw, y+bh], radius=8,
                             fill=(0, 0, 0, int(0.55 * alpha)))
        d.rounded_rectangle([x, y, x+bw, y+bh], radius=8,
                             outline=(*GOLD, alpha), width=2)
        bb  = f.getbbox(txt)
        th  = bb[3] - bb[1]
        # Centre text horizontally inside pill
        tx_ = x + (bw - tw) // 2
        ty_ = y + (bh - th) // 2 - bb[1]
        d.text((tx_, ty_), txt, font=f, fill=(*GOLD, alpha))
    return _over(img, _draw)

def _over(base, fn):
    ov = Image.new('RGBA', base.size, (0,0,0,0))
    fn(ImageDraw.Draw(ov))
    return Image.alpha_composite(base, ov)

def _paste_centred(img, limg, cx, cy):
    if limg is None: return img
    lw,lh = limg.size
    x = max(0, min(cx-lw//2, VIDEO_W-lw))
    y = max(0, min(cy-lh//2, VIDEO_H-lh))
    img.alpha_composite(limg, dest=(x,y))
    return img

def _paste_topleft(img, limg, tx, ty):
    if limg is None: return img
    img.alpha_composite(limg, dest=(max(0,tx), max(0,ty)))
    return img


# ── frame ─────────────────────────────────────────────────────────────────────
def _frame(t: float, rates: dict, st: _State, changes: dict = None) -> np.ndarray:
    img  = Image.fromarray(st.bg(t), 'RGB').convert('RGBA')
    avail = SAFE_R - SAFE_L

    # ── LOGO animation ───────────────────────────────────────────────────────
    CX = VIDEO_W // 2                 # intro/outro centre x
    CY = int(VIDEO_H * 0.375)         # intro/outro centre y

    if t < _LOGO_MOVE[0]:
        # Fade in at centre, large
        a = _p(*_LOGO_FADE, t)
        img = _paste_centred(img, st.logo_img(LOGO_INTRO_H, a), CX, CY)

    elif t < _LOGO_MOVE[1]:
        # Fly from centre to corner
        prog = _pio(*_LOGO_MOVE, t)
        h_now  = int(LOGO_INTRO_H + (LOGO_CORNER_H - LOGO_INTRO_H) * prog)
        li     = st.logo_img(h_now, 1.0)
        if li:
            lw_c  = int(st.logo.size[0] * LOGO_CORNER_H / st.logo.size[1]) if st.logo else LOGO_CORNER_H
            ex    = SAFE_L + lw_c // 2
            ey    = LOGO_Y + LOGO_CORNER_H // 2
            cx_   = int(CX + (ex - CX) * prog)
            cy_   = int(CY + (ey - CY) * prog)
            img   = _paste_centred(img, li, cx_, cy_)

    elif t < _FADE_OUT[0]:
        # Corner, normal size
        img = _paste_topleft(img, st.logo_img(LOGO_CORNER_H, 1.0), SAFE_L, LOGO_Y)
        _lw = int(st.logo.size[0] * LOGO_CORNER_H / st.logo.size[1]) if st.logo else LOGO_CORNER_H
        img = _draw_official_badge(img, SAFE_L, LOGO_Y + LOGO_CORNER_H + 4, 255, logo_w=_lw)

    elif t < _OUTRO_LOGO[0]:
        # Corner, fading out with content
        ca  = 1.0 - _p(*_FADE_OUT, t)
        img = _paste_topleft(img, st.logo_img(LOGO_CORNER_H, ca), SAFE_L, LOGO_Y)
        _lw = int(st.logo.size[0] * LOGO_CORNER_H / st.logo.size[1]) if st.logo else LOGO_CORNER_H
        img = _draw_official_badge(img, SAFE_L, LOGO_Y + LOGO_CORNER_H + 4, int(255*ca), logo_w=_lw)

    else:
        # Fly back to centre, grow
        prog  = _pio(*_OUTRO_LOGO, t)
        h_now = int(LOGO_CORNER_H + (LOGO_INTRO_H - LOGO_CORNER_H) * prog)
        li    = st.logo_img(h_now, 1.0)
        if li and st.logo:
            lw_c  = int(st.logo.size[0] * LOGO_CORNER_H / st.logo.size[1])
            sx    = SAFE_L + lw_c // 2
            sy    = LOGO_Y + LOGO_CORNER_H // 2
            cx_   = int(sx + (CX - sx) * prog)
            cy_   = int(sy + (CY - sy) * prog)
            img   = _paste_centred(img, li, cx_, cy_)

    # ── CONTENT alpha (fades out during outro) ───────────────────────────────
    ca = 1.0 - _p(*_FADE_OUT, t)

    if ca > 0.02:

        # Title  (no underline, slightly smaller)
        p = _p(*_TITLE, t) * ca
        if p > 0:
            a  = int(255*p)
            dy = int((1-min(p/0.5,1))*28)
            fh = _fit("GOLD JEWELLERY RATES", avail, 52, W_EB)
            img = _over(img, lambda d,_f=fh,_a=a,_dy=dy:
                d.text((SAFE_L, TITLE_Y+_dy), "GOLD JEWELLERY RATES",
                       font=_f, fill=(*GOLD,_a)))

        # Subtitle  (bold, full opacity, extra vertical breathing room via Y gaps)
        p = _p(*_SUB, t) * ca
        if p > 0:
            img = _over(img, lambda d,_a=int(255*p):
                d.text((SAFE_L, SUBT_Y), "TODAY'S RETAIL PRICES  ·  AED PER GRAM",
                       font=_font(27, W_BOLD), fill=(*WHITE, int(_a * 0.90))))

        # Date  (full GOLD colour, no opacity reduction)
        p = _p(*_DATE, t) * ca
        if p > 0:
            ts = rates.get('timestamp','')
            try:    ds = datetime.fromisoformat(ts).strftime('%d %B %Y').upper()
            except: ds = datetime.now().strftime('%d %B %Y').upper()
            img = _over(img, lambda d,_s=ds,_a=int(255*p):
                d.text((SAFE_L, DATE_Y), _s, font=_font(28, W_SB), fill=(*GOLD, _a)))

        # Card background with pulse glow
        p = _p(*_CARD, t) * ca
        if p > 0:
            pulse = 0.0
            if _CARD[1] < t < _FADE_OUT[0]:
                pulse = 0.3 + 0.3*math.sin(2*math.pi*t*0.75)
            oa = int((40 + 35*pulse) * min(p,ca))
            img = _over(img, lambda d,_p=p,_oa=oa:
                d.rounded_rectangle([SAFE_L,CARD_Y,SAFE_R,CARD_B],
                    radius=16,
                    fill=(0,0,0,int(125*_p*ca)),
                    outline=(*GOLD,_oa), width=1))

        # Rate rows
        fk  = _font(52, W_EB)   # karat
        fp  = _font(56, W_EB)   # price
        pad = 28

        # Badge: bold arrow font (larger to match visual height of numbers) + Outfit Bold numbers
        fch     = _arrow_font(54)       # arrow glyph — oversized so visual triangle ≈ number height
        fbn     = _font(36, W_BOLD)     # Outfit Bold for the number
        BADGE_W = _tw("▼", fch) + 12 + _tw("99.99", fbn) + 44
        BADGE_H   = 74
        BADGE_GAP = 20

        for i, karat in enumerate(ROWS):
            rs = _ROW_BASE + i * _ROW_GAP
            re = rs + _ROW_DUR
            p_row = _p(rs, re, t)
            if p_row <= 0: continue

            p_vis = p_row * ca
            a     = int(255 * p_vis)
            dx    = int((1 - min(p_row/0.45,1)) * 78)   # slide from right

            # Counter: number ticks up from 60 % → final over 0.55 s
            pc    = _p(rs, rs+0.55, t)
            disp  = rates[karat] * (0.60 + 0.40*pc)

            rt    = CARD_Y + 25 + i*ROW_H
            ty    = rt + (ROW_H-56)//2

            # Badge right edge aligns with SAFE_R - pad
            badge_rx = SAFE_R - pad           # badge right x
            badge_lx = badge_rx - BADGE_W     # badge left x
            badge_ty = rt + (ROW_H - BADGE_H) // 2
            badge_by = badge_ty + BADGE_H

            # Price right-aligns to left of badge (with gap)
            final_s  = f"AED {rates[karat]:,.2f}"
            disp_s   = f"AED {disp:,.2f}"
            pw       = _tw(final_s, fp)
            price_rx = badge_lx - BADGE_GAP   # price right edge
            kx       = SAFE_L + pad + dx
            px_      = price_rx - pw + dx

            # Change badge data for this karat
            chg = changes.get(karat) if changes else None

            def _row(d,
                     _k=karat, _ds=disp_s,
                     _kx=kx, _px=px_, _ty=ty, _rt=rt,
                     _fk=fk, _fp=fp, _fch=fch, _fbn=fbn, _a=a, _i=i,
                     _blx=badge_lx, _bty=badge_ty, _brx=badge_rx, _bby=badge_by,
                     _chg=chg):
                # Gold left accent stripe
                d.rectangle([SAFE_L+1, _rt+14, SAFE_L+5, _rt+ROW_H-14],
                             fill=(*GOLD, _a))
                # Karat label
                d.text((_kx, _ty), _k, font=_fk, fill=(*GOLD, _a))
                # Price (counting up)
                d.text((_px, _ty), _ds, font=_fp, fill=(*WHITE, _a))
                # Change badge (only when change data available)
                if _chg is not None:
                    if _chg > 0:
                        col    = (39, 174, 96)
                        arrow  = "▲"
                        num_s  = f"{_chg:,.2f}"
                    elif _chg < 0:
                        col    = (160, 60, 55)
                        arrow  = "▼"
                        num_s  = f"{abs(_chg):,.2f}"
                    else:
                        col    = (110, 110, 110)
                        arrow  = "—"
                        num_s  = "0.00"

                    # Pill: dark translucent, no border
                    d.rounded_rectangle(
                        [_blx, _bty, _brx, _bby], radius=10,
                        fill=(0, 0, 0, int(_a * 0.50))
                    )

                    # Layout: arrow (large bold) + gap + number (Outfit Bold)
                    aw    = _tw(arrow, _fch)
                    nw    = _tw(num_s, _fbn)
                    gap   = 10
                    ox    = _blx + ((_brx - _blx) - aw - gap - nw) // 2
                    pmid  = (_bty + _bby) // 2

                    # Each glyph centred to pill midpoint via its own bbox
                    abb = _fch.getbbox(arrow)
                    d.text((ox, pmid - (abb[1] + abb[3]) // 2),
                           arrow, font=_fch, fill=(*col, _a))

                    nbb = _fbn.getbbox(num_s)
                    d.text((ox + aw + gap, pmid - (nbb[1] + nbb[3]) // 2),
                           num_s, font=_fbn, fill=(*col, _a))
                # Separator
                if _i < len(ROWS)-1:
                    sy = CARD_Y+25+(_i+1)*ROW_H
                    d.line([(SAFE_L+18,sy),(SAFE_R-18,sy)],
                           fill=(*GOLD, int(38*_a/255)), width=1)
            img = _over(img, _row)

        # Tagline
        p = _p(*_TAG, t) * ca
        if p > 0:
            img = _over(img, lambda d,_a=int(255*p):
                d.text((SAFE_L, TAG_Y),
                       "Updated daily  ·  Dubai Gold & Jewellery Group",
                       font=_font(26, W_BOLD), fill=(*WHITE, int(_a * 0.75))))

    # ── OUTRO URL ────────────────────────────────────────────────────────────
    p = _p(*_URL, t)
    if p > 0:
        a   = int(255*p)
        url = "www.dubaicityofgold.com"
        fu  = _font(46, W_BOLD)
        uw  = _tw(url, fu)
        ux  = (VIDEO_W - uw) // 2

        # Anchor: label sits here, pill starts 20px below label bottom
        label_y = int(VIDEO_H * 0.555)
        pill_t  = label_y + 56      # 56px gap between label and pill
        pill_h  = 84                # tall pill for breathing room
        pill_b  = pill_t + pill_h

        # Vertically centre the URL text inside the pill
        text_bb  = fu.getbbox("AED")          # representative bbox for cap height
        text_h   = text_bb[3] - text_bb[1]
        text_y   = pill_t + (pill_h - text_h) // 2 - text_bb[1]

        # Label  (bold, fully visible)
        fl  = _font(30, W_BOLD)
        lab = "For more information, visit"
        lw  = _tw(lab, fl)
        img = _over(img, lambda d,_f=fl,_l=lab,_lw=lw,_ly=label_y,_a=a:
            d.text(((VIDEO_W-_lw)//2, _ly), _l,
                   font=_f, fill=(*WHITE, int(_a * 0.90))))

        # URL pill background
        img = _over(img, lambda d,_ux=ux,_uw=uw,_pt=pill_t,_pb=pill_b,_a=a:
            d.rounded_rectangle([_ux-28, _pt, _ux+_uw+28, _pb],
                                 radius=14,
                                 fill=(0, 0, 0, int(170*_a/255)),
                                 outline=(*GOLD, int(110*_a/255)), width=2))

        # URL text — typing effect, vertically centred in pill
        chars_shown = int(len(url) * p)
        url_partial = url[:chars_shown] + ("_" if p < 0.98 else "")
        img = _over(img, lambda d,_f=fu,_u=url_partial,_ux=ux,_ty=text_y,_a=a:
            d.text((_ux, _ty), _u, font=_f, fill=(*GOLD_BRIGHT, _a)))

    return np.array(img.convert('RGB'))


# ── Ambient music generator ───────────────────────────────────────────────────
def _make_audio(duration: float = DURATION, sr: int = 44100) -> np.ndarray:
    """
    Generate a cinematic luxury ambient track:
    - Deep A-minor drone (bass + harmonics)
    - Slow golden shimmer (high-freq overtones with gentle swell)
    - Soft bell/chime melody on A-pentatonic minor
    - 1-second fade-in / 1.5-second fade-out
    """
    n = int(sr * duration)
    t = np.arange(n, dtype=np.float64) / sr
    audio = np.zeros(n, dtype=np.float64)

    # ── Drone layer  (A-minor: A C E) ────────────────────────────────────────
    for freq, amp in [(55.0,0.28),(110.0,0.18),(130.81,0.10),
                      (164.81,0.09),(220.0,0.06),(261.63,0.04)]:
        audio += amp * np.sin(2*math.pi*freq*t)

    # ── Shimmer layer  (high harmonics, slow amplitude swell) ────────────────
    swell = 0.65 + 0.35 * np.sin(2*math.pi*0.18*t + 0.5)
    for freq, amp in [(880.0,0.025),(1760.0,0.015),(2637.0,0.008)]:
        audio += amp * swell * np.sin(2*math.pi*freq*t)

    # ── Bell/chime melody on A-pentatonic minor ───────────────────────────────
    # Notes (Hz):  A4=440  C5=523.25  D5=587.33  E5=659.25  G5=783.99
    BELLS = [
        (0.8,  440.0,  0.14), (2.0,  523.25, 0.12), (3.4,  659.25, 0.13),
        (4.6,  523.25, 0.11), (5.6,  440.0,  0.12), (6.8,  587.33, 0.11),
        (7.8,  659.25, 0.13), (8.9,  523.25, 0.10), (9.8,  440.0,  0.14),
        (10.6, 783.99, 0.09), (11.5, 659.25, 0.08),
    ]
    for onset, freq, amp in BELLS:
        s = int(onset * sr)
        dur_s = min(int(2.0 * sr), n - s)
        if dur_s <= 0: continue
        bt = np.arange(dur_s, dtype=np.float64) / sr
        # Bell ADSR: 15ms attack, exponential decay
        atk = int(0.015 * sr)
        env = np.exp(-bt * 2.8)
        env[:atk] = np.linspace(0, 1, atk)
        tone  = np.sin(2*math.pi*freq*bt)
        tone += 0.35 * np.sin(2*math.pi*freq*2.0*bt)   # 2nd harmonic
        tone += 0.15 * np.sin(2*math.pi*freq*2.756*bt)  # inharmonic overtone
        audio[s:s+dur_s] += amp * env * tone

    # ── Global swell (very slow, adds life) ──────────────────────────────────
    audio *= (0.80 + 0.20 * np.sin(2*math.pi*0.08*t))

    # ── Fade in / fade out ────────────────────────────────────────────────────
    fi = int(1.0 * sr); fo = int(1.5 * sr)
    audio[:fi] *= np.linspace(0, 1, fi)
    if n > fo: audio[-fo:] *= np.linspace(1, 0, fo)

    # ── Normalise ─────────────────────────────────────────────────────────────
    peak = np.max(np.abs(audio))
    if peak > 0: audio = audio / peak * 0.72

    return audio.astype(np.float32)


# ── public API ────────────────────────────────────────────────────────────────
def generate_video(rates: dict, output_path: str,
                   bg_index: int = -1, changes: dict = None) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    st = _State(bg_index=bg_index)

    def make_frame(t: float) -> np.ndarray:
        return _frame(t, rates, st, changes)

    clip = mpy.VideoClip(make_frame, duration=DURATION)

    # ── Audio: prefer music.mp3 in assets, fall back to generated ambient ─────
    _MUSIC = os.path.join(_A, 'music.mp3')
    try:
        if os.path.exists(_MUSIC):
            aclip = mpy.AudioFileClip(_MUSIC)
            # Trim or loop to match video duration
            if aclip.duration < DURATION:
                aclip = aclip.audio_loop(duration=DURATION)
            else:
                aclip = aclip.subclip(0, DURATION)
            # 0.8s fade-in, 1.2s fade-out
            aclip = aclip.audio_fadein(0.8).audio_fadeout(1.2)
            clip  = clip.set_audio(aclip)
            print(f"[audio] {os.path.basename(_MUSIC)}")
        else:
            from moviepy.audio.AudioClip import AudioArrayClip
            raw    = _make_audio(DURATION)
            stereo = np.column_stack([raw, raw])
            aclip  = AudioArrayClip(stereo, fps=44100)
            clip   = clip.set_audio(aclip)
            print("[audio] ambient track (generated)")
    except Exception as e:
        print(f"[audio] skipped ({e})")

    clip.write_videofile(output_path, fps=FPS, codec='libx264',
                         audio=True, audio_codec='aac',
                         ffmpeg_params=['-pix_fmt','yuv420p'],
                         logger=None)

    # Release background video resource
    if getattr(st, 'has_v', False) and st.vid:
        st.vid.close()

    return output_path
