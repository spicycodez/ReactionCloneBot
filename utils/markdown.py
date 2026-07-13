def escape_markdown(text: str) -> str:
    """
    Any text that comes from the user or the chat itself (first name,
    chat title, etc.) can contain raw markdown-special characters
    (*, _, `, [). If that text gets interpolated straight into a
    **bold**/`code`-style template, Pyrogram's markdown-entity parser
    can end up unbalanced and Telegram rejects the send with
    400 ENTITY_BOUNDS_INVALID. Escaping these characters before
    formatting avoids that.
    """
    if not text:
        return ""
    for ch in ("\\", "_", "*", "`", "["):
        text = text.replace(ch, f"\\{ch}")
    return text
