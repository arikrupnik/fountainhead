# fountainhead.py: parses Fountain screenplays, outputs semantic XML

import sys
import re
import xml.etree.ElementTree as ET

# fountain source element types
SCENEHEADING = "scene-heading"
ACTION = "action"
CHARACTER = "character"
DIALOGUE = "dialogue"
PARENTHETICAL = "parenthetical"
TRANSITION = "transition"
NOTE = "note"
BONEYARD = "boneyard"
SECTIONHEADING = "h"
SYNOPSIS = "synopsis"
PAGEBREAK = "page-break"


def parse(lines):
    doc=ET.Element("fountain")
    lines=map(lambda l: l.rstrip("\r\n"), lines)
    title, body = split_title_body(lines)
    ptitle=parse_title(title)
    body, notes = parse_comments_notes(body)
    pbody=parse_body(body)
    if title:
        et=ET.SubElement(doc, "title-page")
        for key in ptitle:
            ek=ET.SubElement(et, "key")
            ek.set("name", key[0])
            for value in key[1:]:
                ET.SubElement(ek, "value").text=value
    for pline in pbody:
        ET.SubElement(doc, pline.t).text=pline.s
    return doc

def split_title_body(lines):
    lines=discard_leading_empty_lines(lines)
    if not len(lines):
        # nothing at all
        return ((),())
    if (lines[0]!=lines[0].lstrip()) or \
       (not ":" in lines[0]) or \
       (re.search(r"[^\w ]", lines[0].split(":")[0])) or \
       (lines[0].strip().upper()=="FADE IN:"):
        # no title page
        return ((),lines)
    title_lines=[]
    for n, l in enumerate(lines):
        title_lines+=[l]
        if n>0 and not title_lines[-1] and not title_lines[-2]:
            return (title_lines[:-2], discard_leading_empty_lines(lines[n+1:]))
    # title page only
    return (title_lines, ())

def discard_leading_empty_lines(lines):
    for n, l in enumerate(lines):
        if l:
            return lines[n:]
    return []

def parse_title(lines):
    # "Information is encoding (sic) in the format key: value. Keys
    # can have spaces (e. g. Draft date), but must end with a colon."
    rawkeys=[]
    for l in lines:
        if l==l.lstrip():
            rawkeys.append(l.split(":", 1))
        else:
            rawkeys[-1].append(l)
    keys=[]
    for k in rawkeys:
        keys.append(filter(lambda s: s, map(lambda s: s.strip(), k)))
    return keys

def parse_comments_notes(lines):
    text="\n".join(lines)
    text=re.sub(r"(/\*.*?\*/)", "", text, flags=re.DOTALL)
    out_text=""
    notes=[]
    for token in re.split(r"(\[\[.*?\]\])", text, flags=re.DOTALL):
        if token.startswith("[[") and token.endswith("]]"):
            out_text+="[["+str(len(notes))+"]]"
            notes+=[token.lstrip("[[").rstrip("]]")]
        else:
            out_text+=token
    return out_text.split("\n"), notes


class tstr(object):
    def __init__(self, t, s):
        self.t=t
        self.s=s

def parse_body(lines):
    # this loop is a little awkward; it must accomodate fountain
    # requirements for lookback and lookahead ("A Scene Heading is any
    # line that has a blank line following it")
    if not len(lines):
        return None
    plines=[]
    prevline=tstr(None, "")
    line = lines[0]
    for nextline in lines[1:]:
        pline=parse_line(line, prevline, nextline)
        if pline.t:
            plines+=[pline]
        prevline=pline
        line=nextline
    nextline=None
    pline=parse_line(line, prevline, nextline)
    if pline.t:
        plines+=[pline]
    plines=consolidate_consecutive(plines, (ACTION, DIALOGUE))
    return plines

def parse_line(line, prevline, nextline):
    if not line:
        # whitespace, including empty lines, is meaningful inside ACTION
        if prevline.t==ACTION:
            return tstr(ACTION, line)
        else:
            return tstr(None, line)
    
    sline = line.strip()
    
    # first, I consider forcing elements
    # "Note that only a single leading period followed by an
    # alphanumeric character will force a Scene Heading. This allows
    # the writer to begin Action and Dialogue elements with ellipses
    # without worry that they'll be interpreted as Scene Headings."
    if sline.startswith(".") and not sline.startswith(".."):
        return tstr(SCENEHEADING, sline[1:].lstrip())
    if sline.startswith("!"):
        return tstr(ACTION, sline[1:])
    if sline.startswith("@"):
        return tstr(CHARACTER, sline[1:].lstrip())
    if sline.startswith(">") and not sline.endswith("<"):
        return tstr(TRANSITION, sline[1:].lstrip())

    # next, handle context-free elements
    if sline.startswith("#"):
        #If there are capturing groups in the separator and it matches
        #at the start of the string, the result will start with an
        #empty string.
        _,marker,text=re.split(r"(#{1,6})", sline, maxsplit=1)
        return tstr(SECTIONHEADING+str(len(marker)), text.strip())
    # page breaks may look like synopses, so I process them first
    if re.match(r"^===+$", sline):
        return tstr(PAGEBREAK, "")
    if sline.startswith("="):
        return tstr(SYNOPSIS, sline[1:].lstrip())

    # next, elements that require lookahead or lookback
    
    # "A Scene Heading is any line that has a blank line following it,
    # and either begins with INT or EXT or similar (full list
    # below). A Scene Heading always has at least one blank line
    # preceding it."
    # "A line beginning with any of the following, followed by either a
    # dot or a space, is considered a Scene Heading (unless the line
    # is preceded by an exclamation point !). Case insensitive.
    # INT  EXT  EST  INT./EXT  INT/EXT  I/E"
    if not prevline.s:
        if not nextline:
            token = re.split(r"[\. ]", sline+" ")[0].upper()
            if token in ("INT", "EXT", "EST", "INT/EXT", "I/E"):
                return tstr(SCENEHEADING, sline)

    # "A Character element is any line entirely in uppercase, with one
    # empty line before it and without an empty line after it."
    if not prevline.s:
        if nextline:
            if line.upper()==line:
                # "Character names must include at least one
                # alphabetical character. "R2D2" works, but "23" does
                # not."
                if re.sub(r"[0-9_]", "", re.sub(r"\W", "", line)):
                    return tstr(CHARACTER, sline)
                # "The requirements for Transition elements are:
                # Uppercase; Preceded by and followed by an empty
                # line; Ending in TO:"
                if line.endswith("TO:"):
                    return tstr(TRANSITION, sline)

    # "Parentheticals follow a Character or Dialogue element, and are
    # wrapped in parentheses ()."
    if prevline.t in (CHARACTER, PARENTHETICAL, DIALOGUE):
        if re.match(r"^\(.*\)$", sline):
            return tstr(PARENTHETICAL, sline)
        else:
            # "Dialogue is any text following a Character or Parenthetical element."
            return tstr(DIALOGUE, sline)

    # finally, "Action, or scene description, is any paragraph that
    # doesn't meet criteria for another element"
    return tstr(ACTION, line)

def consolidate_consecutive(plines, element_names):
    # this has to happen in a separate step; action lines can come
    # from separate code branches (forced or not) and consolidating
    # them at parsing would require duplicating code among those
    # branches
    result=[]
    for p in plines:
        if result and p.t in element_names and result[-1].t==p.t:
            result[-1].s+="\n"+p.s
        else:
            result+=[p]
    return result

# TODO: formatting: including inlines
# TODO: formatting: center
# TODO: lyrics
# TODO: dual dialogue
# TODO: scene numbers
# TODO: reconstitute notes and clean up linefeeds around them
# TODO: reconstitute structure (sections, scenes)
# TODO: character extensions
    
def main(argv):
    print ET.tostring(parse(open(argv[1])))

if __name__ == "__main__":
    main(sys.argv)
