"""TEXT and XML renderers (one plotOn, selected by mode bits).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:315-419 (plotOn), Player.java:99-119 (drawSelf),
Message.java:126-182 (drawSelf), Message.java:192-224 (printComment).
One buffer line at a time, exactly like the Java char[].
"""

import io

from callplot.constants import Mode
from callplot.errors import NumberFormatError
from callplot.flow import Flow
from callplot.jcompat import CharBuf, arr_at, fmt_i, idiv, parse_java_int
from callplot.model import Message, Player


def text_on(f: Flow, mode: Mode) -> str:
    """Flow.java:315-419 (prologue/epilogue; the line loop is below).

    DESIGN-PYTHON.md section 3.7: the entry builds its own io.StringIO and
    returns the whole output as one str.
    """
    out = io.StringIO()
    if (mode & Mode.XML) != 0:
        out.write(("<plot>") + "\n")  # Flow.java:318-319
        out.write(("<picture>") + "\n")

    lines = draw_text_lines(f, mode, None)  # numbering side effect: myNumber
    for line in lines:
        out.write((line) + "\n")

    if (mode & Mode.XML) != 0:
        out.write(("</picture>") + "\n")  # Flow.java:401-403
        for m in f.messages:
            print_comment(m, out)
        out.write(("</plot>") + "\n")
    return out.getvalue()


def draw_text_lines(f: Flow, mode: Mode, force_links: bool | None) -> list[str]:
    """Flow.java:320-399: the picture-content line loop.  Returns the lines
    instead of writing them so the table pipeline (section 3.13.1) can reuse
    them.  forceLinks: True forces links on (tables), False forces off, none
    keeps Flow.links.  The loop runs startMessageNumbers first, exactly like
    Java, so drawMessage's myNumber assignment is visible to callers."""
    f.start_message_numbers()
    links = f.links if force_links is None else force_links

    width = f.get_total_width()
    buf = CharBuf(width)
    lines = []

    for line in range(0, f.get_total_height() + 1):
        for i in range(width):
            buf.set(i, " ")

        for p in f.players:
            draw_player(f, p, line, buf)
        for m in f.messages:
            draw_message(f, m, line, buf)

        if f.should_print(buf):
            last_char = width - 1
            while buf.get(last_char) == " " and last_char > 0:
                last_char -= 1

            if (mode & Mode.XML) != 0:
                lines.append(write_line_xml(f, buf, last_char, links))
            else:
                lines.append(buf.slice_string(0, last_char + 1))
    return lines


def write_line_xml(f: Flow, buf: CharBuf, last_char: int, links: bool) -> str:
    """Flow.java:359-395: XML-escape and turn (n) into links.  Reproduces
    the switch fallthrough: '(' falls to default unless the try block breaks."""
    s = []
    i = 0
    while i <= last_char:
        ch = buf.get(i)
        wrote = False
        if ch == "<":
            s.append("&lt;")  # Flow.java:365
            wrote = True
        elif ch == ">":
            s.append("&gt;")  # Flow.java:369
            wrote = True
        elif ch == "(" and links:
            num_start = i + 1
            while i <= last_char and buf.get(i) != ")":
                i += 1
            linked = False
            if buf.get(i) == ")":
                # buf.get may raise IndexError: Java's lineBuffer[i] would
                # be an array-index-out-of-bounds error.
                try:
                    num = parse_java_int(buf.slice_string(num_start, i - num_start))
                    s.append(
                        "(<a href='#t"
                        + fmt_i(num)
                        + "'>"
                        + fmt_i(num)
                        + "</a>)<a name='m"
                        + fmt_i(num)
                        + "'/>"
                    )
                    linked = True  # break out of the switch (Flow.java:383)
                except NumberFormatError:
                    pass  # Flow.java:384-385: swallow, fall through to i--
            if linked:
                i += 1  # JS: continue, then the loop's i++ is skipped: land
                # on the char after ')'
                continue
            i = num_start - 1
        if not wrote:
            s.append(buf.get(i))  # default: Flow.java:392
        i += 1
    return "".join(s)


def draw_player(f: Flow, p: Player, line: int, buf: CharBuf) -> None:
    """Player.java:99-119"""
    line_in_caption = f.label_line(line)
    if line_in_caption >= 0:
        # blank = arrayOf(" ") (Player.java:51): one space
        image = p.caption[line_in_caption] if line_in_caption < len(p.caption) else " "
    else:
        image = "|"  # glyph (Player.java:50)
    if len(image) == 1:
        buf.set(p.column, image[0])
    else:
        bias = idiv(len(image), 2)
        buf.copy_in(image, p.column - bias, len(image))


def draw_message(f: Flow, m: Message, line: int, buf: CharBuf) -> None:
    """Message.java:126-182"""
    fcol = f.column_of(m.from_)
    tcol = f.column_of(m.to)
    locol = fcol if fcol < tcol else tcol
    hicol = tcol if fcol < tcol else fcol

    offset = m.line - line

    if offset == 0 and locol != hicol:
        for j in range(locol + 1, hicol):
            buf.set(j, m.filler)
        if (m.arrow_from and locol == fcol) or (m.arrow_to and locol == tcol):
            buf.set(locol + 1, "<")
        if (m.arrow_from and hicol == fcol) or (m.arrow_to and hicol == tcol):
            buf.set(hicol - 1, ">")
    elif offset == len(m.caption) and (locol != hicol or f.get_do_note_numbering()):
        num = f.next_message_number()
        if num != -1:
            m.my_number = num
            final_caption = "(" + fmt_i(num) + ") " + arr_at(m.caption, 0)
        else:
            final_caption = arr_at(m.caption, 0)
        copy_caption(buf, locol, final_caption)
    elif 0 < offset <= len(m.caption):
        idx = len(m.caption) - offset
        copy_caption(buf, locol, arr_at(m.caption, idx))


def copy_caption(buf: CharBuf, locol: int, text: str) -> None:
    """Message.java:162-169 and 173-180: clamp the copy, mark truncation with '*'"""
    width = len(buf.a)
    copy_size = len(text)
    if locol + 1 + len(text) > width:
        copy_size = width - (locol + 1)
    buf.copy_in(text, locol + 1, copy_size)
    if copy_size != len(text):
        buf.set(width - 1, "*")


def print_comment(m: Message, out: io.StringIO) -> None:
    """Message.java:192-224 (XML epilogue; the Graffle epilogue shares it)"""
    if m.my_number != 0:
        out.write(("<message>") + "\n")
        out.write(("<number>" + fmt_i(m.my_number) + "</number>") + "\n")
        out.write(("<captions>") + "\n")
        for i in range(len(m.caption)):
            out.write(("<caption>" + m.caption[i] + "</caption>") + "\n")
        out.write(("</captions>") + "\n")
        out.write(("<notes>") + "\n")
        for c in m.notes:
            out.write(("<note>") + "\n")
            out.write((c) + "\n")
            out.write(("</note>") + "\n")
        out.write(("</notes>") + "\n")
        out.write(("<comments>") + "\n")
        for c in m.comments:
            out.write(("<comment>") + "\n")
            out.write((c) + "\n")
            out.write(("</comment>") + "\n")
        out.write(("</comments>") + "\n")
        out.write(("</message>") + "\n")
