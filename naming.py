# naming.py
"""File-name styles for uploaded screenshots.

imgbb shows (and serves) the picture under the `name` we send with the upload.
Style "default" sends no name at all, which is the old behaviour: imgbb picks
its own name and the upload carries no extra naming data.

Every other style builds a name from the current local time, the image size,
a counter, a random id, etc. An optional custom prefix goes in front of any
style, and the extension (.png / .webp / .jpg) can be appended on request.
"""
import hashlib
import re
import secrets
import uuid
from datetime import datetime

DEFAULT_STYLE = "default"

EXT_BY_FORMAT = {"WEBP": "webp", "PNG": "png", "JPEG": "jpg"}

# Fixed sample used only to show an example next to each menu entry.
SAMPLE_CTX = {
    "now": datetime(2026, 10, 25, 14, 30, 45, 123000),
    "w": 1920,
    "h": 1080,
    "data": b"sample",
    "counter": 7,
}

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def _t(fmt):
    """Style that is just a strftime pattern."""
    return lambda c: c["now"].strftime(fmt)


def _ms(c):
    return f"{c['now'].microsecond // 1000:03d}"


def _epoch(c):
    return str(int(c["now"].timestamp()))


def _epoch_ms(c):
    return str(int(c["now"].timestamp() * 1000))


def _size(c):
    return f"{c['w']}x{c['h']}"


# (group, style_id, uses_counter, builder)
STYLES = [
    # ---------------------------------------------------------- Basic
    ("Basic", "default", False, None),  # no name sent
    ("Basic", "image", False, lambda c: "image"),
    ("Basic", "screenshot", False, lambda c: "screenshot"),
    ("Basic", "screen", False, lambda c: "screen"),
    ("Basic", "capture", False, lambda c: "capture"),

    # ------------------------------------------------- Date + time
    ("Date + time", "dt_under", False, _t("%Y-%m-%d_%H-%M-%S")),
    ("Date + time", "dt_compact", False, _t("%Y%m%d_%H%M%S")),
    ("Date + time", "dt_solid", False, _t("%Y%m%d%H%M%S")),
    ("Date + time", "dt_dash", False, _t("%Y-%m-%d-%H-%M-%S")),
    ("Date + time", "dt_dot", False, _t("%Y.%m.%d_%H.%M.%S")),
    ("Date + time", "dt_space", False, _t("%Y-%m-%d %H-%M-%S")),
    ("Date + time", "dt_iso", False, _t("%Y-%m-%dT%H-%M-%S")),
    ("Date + time", "dt_short", False, _t("%y%m%d_%H%M%S")),
    ("Date + time", "dt_ms", False, lambda c: c["now"].strftime("%Y-%m-%d_%H-%M-%S-") + _ms(c)),
    ("Date + time", "dt_ru", False, _t("%d-%m-%Y_%H-%M-%S")),
    ("Date + time", "dt_ru_dot", False, _t("%d.%m.%Y_%H.%M.%S")),
    ("Date + time", "dt_us", False, _t("%m-%d-%Y_%H-%M-%S")),
    ("Date + time", "dt_month_name", False, _t("%d-%b-%Y_%H-%M-%S")),
    ("Date + time", "dt_weekday", False, _t("%a_%Y-%m-%d_%H-%M-%S")),
    ("Date + time", "dt_12h", False, _t("%Y-%m-%d_%I-%M-%S%p")),

    # ------------------------------------------------------ Time only
    ("Time only", "t_dash", False, _t("%H-%M-%S")),
    ("Time only", "t_solid", False, _t("%H%M%S")),
    ("Time only", "t_dot", False, _t("%H.%M.%S")),
    ("Time only", "t_colon_safe", False, _t("%Hh%Mm%Ss")),
    ("Time only", "t_ms", False, lambda c: c["now"].strftime("%H-%M-%S-") + _ms(c)),
    ("Time only", "t_hm", False, _t("%H-%M")),
    ("Time only", "t_12h", False, _t("%I-%M-%S%p")),

    # ------------------------------------------------------ Date only
    ("Date only", "d_iso", False, _t("%Y-%m-%d")),
    ("Date only", "d_compact", False, _t("%Y%m%d")),
    ("Date only", "d_ru", False, _t("%d-%m-%Y")),
    ("Date only", "d_ru_dot", False, _t("%d.%m.%Y")),
    ("Date only", "d_month_name", False, _t("%d-%b-%Y")),

    # ----------------------------------------- Linux / OS-like styles
    # scrot: date with hyphens, time written solid
    ("Linux / OS style", "lx_dash_solid", False, _t("%Y-%m-%d-%H%M%S")),
    ("Linux / OS style", "lx_scrot", False, lambda c: c["now"].strftime("%Y-%m-%d-%H%M%S_") + _size(c) + "_scrot"),
    ("Linux / OS style", "lx_gnome", False, _t("Screenshot from %Y-%m-%d %H-%M-%S")),
    ("Linux / OS style", "lx_spectacle", False, _t("Screenshot_%Y%m%d_%H%M%S")),
    ("Linux / OS style", "lx_epoch", False, _epoch),
    ("Linux / OS style", "lx_epoch_ms", False, _epoch_ms),
    ("Linux / OS style", "win_snip", False, _t("Screenshot %Y-%m-%d %H%M%S")),
    ("Linux / OS style", "win_counter", True, lambda c: f"Screenshot ({c['counter']})"),
    ("Linux / OS style", "mac", False, _t("Screenshot %Y-%m-%d at %H.%M.%S")),

    # ---------------------------------------------- Unique / counters
    ("Unique / counter", "counter", True, lambda c: f"{c['counter']:04d}"),
    ("Unique / counter", "image_counter", True, lambda c: f"image_{c['counter']:04d}"),
    ("Unique / counter", "shot_counter", True, lambda c: f"screenshot_{c['counter']:04d}"),
    ("Unique / counter", "rand8", False, lambda c: secrets.token_hex(4)),
    ("Unique / counter", "rand16", False, lambda c: secrets.token_hex(8)),
    ("Unique / counter", "uuid", False, lambda c: str(uuid.uuid4())),
    ("Unique / counter", "hash", False, lambda c: hashlib.sha1(c["data"]).hexdigest()[:12]),
    ("Unique / counter", "dt_rand", False, lambda c: c["now"].strftime("%Y%m%d_%H%M%S_") + secrets.token_hex(2)),

    # ------------------------------------------------- With image size
    ("With image size", "size", False, _size),
    ("With image size", "dt_size", False, lambda c: c["now"].strftime("%Y-%m-%d_%H-%M-%S_") + _size(c)),
    ("With image size", "image_size", False, lambda c: f"image_{_size(c)}"),
    ("With image size", "t_size", False, lambda c: c["now"].strftime("%H-%M-%S_") + _size(c)),
]

_BY_ID = {sid: (group, uses_counter, fn) for group, sid, uses_counter, fn in STYLES}


def groups():
    """Group names in menu order."""
    seen = []
    for group, _sid, _uc, _fn in STYLES:
        if group not in seen:
            seen.append(group)
    return seen


def styles_in_group(group):
    return [sid for g, sid, _uc, _fn in STYLES if g == group]


def sanitize(text):
    text = _INVALID_CHARS.sub("_", text).strip()
    return text[:100]


def _join_prefix(prefix, body):
    if not prefix:
        return body
    # Don't double up the separator if the prefix already ends with one
    if prefix[-1] in "_-. ":
        return prefix + body
    return f"{prefix}_{body}"


def sample(style_id, prefix="", with_ext=False, ext="png"):
    """Example name for the menu (fixed sample date, so it never goes stale)."""
    entry = _BY_ID.get(style_id)
    if not entry or entry[2] is None:
        return "(no name sent - imgbb default)"
    body = entry[2](SAMPLE_CTX)
    name = sanitize(_join_prefix(sanitize(prefix), body))
    return f"{name}.{ext}" if with_ext else name


def uses_counter(style_id):
    entry = _BY_ID.get(style_id)
    return bool(entry and entry[1])


def build_name(config, size, image_bytes):
    """Return the name to send to imgbb, or None for the default style.

    Bumps (and saves) config.filename_counter for counter-based styles.
    """
    style_id = config.filename_style
    entry = _BY_ID.get(style_id)
    if not entry or entry[2] is None:
        return None

    if entry[1]:  # counter style
        config.filename_counter += 1
        config.save()

    ctx = {
        "now": datetime.now(),
        "w": size[0],
        "h": size[1],
        "data": image_bytes,
        "counter": config.filename_counter,
    }
    name = sanitize(_join_prefix(sanitize(config.filename_prefix), entry[2](ctx)))
    if not name:
        return None

    if config.filename_ext:
        name += "." + EXT_BY_FORMAT.get(config.image_format, "png")
    return name
