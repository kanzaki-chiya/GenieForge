"""genieutils-py 的字符串 latin-1 双向补丁。

决定版 dat 内部的字符串是自定义单字节编码，而 genieutils-py 默认按 UTF-8
处理，直接读写会损坏非 ASCII 字符串（中文名等）。本模块对
``String.from_bytes`` / ``String.to_bytes`` / ``GenieClass.write_debug_string``
三处做 monkey-patch，让字符串字节级透传，实现「字节级无损」往返。

用法：在 load / save 之前调用 :func:`apply`（幂等，可重复调用）。
本模块内容来自仓库根目录的 PoC ``genie_poc.py`` 中的 ``apply_string_fix()``。
"""

_applied = False


def apply() -> None:
    """应用 latin-1 双向补丁（幂等）。"""
    global _applied
    if _applied:
        return

    import genieutils.datatypes as dt
    from genieutils.common import GenieClass

    dt.String.from_bytes = staticmethod(
        lambda content: bytes(content).rstrip(b"\0").decode("latin-1")
    )

    def _to_bytes_latin(content, length=None):
        encoded = content.encode("latin-1")
        if not length:
            length = len(encoded) + 1
        return encoded + (b"\0" * (length - len(encoded)))

    dt.String.to_bytes = staticmethod(_to_bytes_latin)

    def _wds_latin(self, value):
        encoded = value.encode("latin-1")
        return (
            self.write_int_16(0x0A60, signed=False)
            + self.write_int_16(len(encoded), signed=False)
            + encoded
        )

    GenieClass.write_debug_string = _wds_latin
    _applied = True
