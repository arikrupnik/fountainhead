# fountainhead.py: parses Fountain screenplays, outputs semantic XML

import sys
import re
import codecs
import xml.etree.ElementTree as ET
import markdown
import markdown.inlinepatterns as ip

# fountain source element types
TITLE_PAGE = "title-page"

SCENE_HEADING = "scene-heading"
ACTION = "action"
CHARACTER = "character"
EXTENSION = "extension"         # the spec alludes to this without calling it an element
DIALOGUE = "dialogue"
PARENTHETICAL = "parenthetical"
TRANSITION = "transition"
NOTE = "note"
BONEYARD = "boneyard"
SECTION_HEADING = "section-heading"
SYNOPSIS = "synopsis"
PAGE_BREAK = "page-break"


def parse(lines):
    doc=ET.Element("fountain")
    lines=map(lambda l: l.rstrip("\r\n"), lines)
    title, body = split_title_body(lines)
    parse_title(title, doc)
    body, notes = parse_comments_notes(body)
    pbody=parse_body(body, doc)
    doc=parse_inlines(doc)
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
    # title page present, need to find where it ends
    for n, l in enumerate(lines):
        if not l:
            return (lines[:n], lines[n:])
    # title page only
    return (lines, ())

def discard_leading_empty_lines(lines):
    for n, l in enumerate(lines):
        if l:
            return lines[n:]
    return []

def parse_title(lines, doc):
    # "Information is encoding (sic) in the format key: value. Keys
    # can have spaces (e. g. Draft date), but must end with a colon."
    if lines:
        et=ET.SubElement(doc, TITLE_PAGE)
        for l in lines:
            # "Values can be inline with the key or they can be
            # indented on a newline below the key (as shown with
            # Contact above). Indenting is 3 or more spaces, or a
            # tab. The indenting pattern allows multiple values for
            # the same key (multiple authors, multiple address
            # lines)."
            if l==l.lstrip():
                key, value=l.split(":", 1)
                ek=ET.SubElement(et, "key")
                ek.set("name", key)
                if value:
                    ET.SubElement(ek, "value").text=value.strip()
            else:
                ET.SubElement(ek, "value").text=l.strip()

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

# Parsing lines of text into text-only elements

def parse_body(lines, doc):
    # this loop is a little awkward; it must accomodate fountain
    # requirements for lookback and lookahead ("A Scene Heading is any
    # line that has a blank line following it")
    if not len(lines):
        return
    line = lines[0]
    for nextline in lines[1:]:
        parse_line(line, doc, nextline)
        line=nextline
    parse_line(line, doc, None)

def parse_line(line, doc, nextline):
    sline = line.strip()
    
    # first, I consider forcing elements
    
    # "Note that only a single leading period followed by an
    # alphanumeric character will force a Scene Heading. This allows
    # the writer to begin Action and Dialogue elements with ellipses
    # without worry that they'll be interpreted as Scene Headings."
    if sline.startswith(".") and not sline.startswith(".."):
        return push_scene_heading(doc, sline[1:].lstrip())
    if sline.startswith("!"):
        return push_element(doc, ACTION, sline[1:])
    if sline.startswith("@"):
        return push_character(doc, sline[1:].lstrip())
    if sline.startswith(">") and not sline.endswith("<"):
        return push_element(doc, TRANSITION, sline[1:].lstrip())

    # next, I handle context-free elements
    
    if sline.startswith("#"):
        # "If there are capturing groups in the separator and it
        # matches at the start of the string, the result will start
        # with an empty string."
        _,marker,text=re.split(r"(#{1,6})", sline, maxsplit=1)
        return push_section_heading(doc, len(marker), text.strip())
    # page breaks may look like synopses, so I process them first
    if re.match(r"^===+$", sline):
        return push_element(doc, PAGE_BREAK, "")
    if sline.startswith("="):
        return push_element(doc, SYNOPSIS, sline[1:].lstrip())

    # next, elements that require lookahead or lookback
    
    # "A Scene Heading is any line that has a blank line following it,
    # and either begins with INT or EXT or similar (full list
    # below). A Scene Heading always has at least one blank line
    # preceding it."
    # "A line beginning with any of the following, followed by either a
    # dot or a space, is considered a Scene Heading (unless the line
    # is preceded by an exclamation point !). Case insensitive.
    # INT  EXT  EST  INT./EXT  INT/EXT  I/E"
    if last_line_empty(doc):
        if not nextline:
            token = re.split(r"[\. ]", sline+" ")[0].upper()
            if token in ("INT", "EXT", "EST", "INT/EXT", "I/E"):
                return push_scene_heading(doc, sline)
            if line.upper()==line:
                # "The requirements for Transition elements are:
                # Uppercase; Preceded by and followed by an empty
                # line; Ending in TO:"
                if line.endswith("TO:"):
                    return push_element(doc, TRANSITION, sline)

    # "A Character element is any line entirely in uppercase, with one
    # empty line before it and without an empty line after it."
    if last_line_empty(doc):
        if nextline:
            if line.upper()==line:
                # "Character names must include at least one
                # alphabetical character. "R2D2" works, but "23" does
                # not."
                if re.sub(r"[0-9_]", "", re.sub(r"\W", "", line)):
                    return push_character(doc, sline)

    # "Dialogue is any text following a Character or Parenthetical
    # element." (really, any non-empty line -ak)
    # "Parentheticals follow a Character or Dialogue element, and are
    # wrapped in parentheses ()."
    if line and len(doc) and doc[-1].tag in (CHARACTER, EXTENSION, PARENTHETICAL, DIALOGUE):
        if re.match(r"^\(.*\)$", sline):
            return push_element(doc, PARENTHETICAL, sline)
        else:
            return push_element(doc, DIALOGUE, sline)
    
    # finally, "Action, or scene description, is any paragraph that
    # doesn't meet criteria for another element"
    return push_element(doc, ACTION, line)

def last_line_empty(elements):
    if not len(elements):
        return True
    elif elements[-1].tag in (
            TITLE_PAGE, PAGE_BREAK, # first line on a page has no preceeding line
            SYNOPSIS, SECTION_HEADING, # removing these leaves empty lines
            SCENE_HEADING, TRANSITION # require empty line in source, imply one in tree
    ):
        return True
    else:
        return (not elements[-1].text) or elements[-1].text.endswith("\n")

def push_element(parent, tag, text):
    if tag in (ACTION, DIALOGUE) and len(parent) and parent[-1].tag==tag:
        # append line to multi-line elements
        parent[-1].text+="\n"+text
        e=parent[-1]
    else:
        if len(parent) and parent[-1].tag==ACTION and not parent[-1].text:
            # remove empty <action /> that comes from individual empty lines
            parent.remove(parent[-1])
        e=ET.SubElement(parent, tag)
        e.text=text
    return e

def push_scene_heading(parent, text):
    tokens=re.split(r"(#.*?#$)", text)
    if len(tokens)==1:
        e=push_element(parent, SCENE_HEADING, text)
    else:
        e=push_element(parent, SCENE_HEADING, tokens[0].strip())
        e.set("id", tokens[1].strip("#"))
    return e

def push_character(parent, text):
    if text.endswith("^"):
        dual=True
        text=text[:-1].strip()
    else:
        dual=False
    tokens=filter(lambda s: s,
                  map(lambda s: s.strip(),
                      re.split(r"(\(.*?\))", text)))
    e=push_element(parent, CHARACTER, tokens[0])
    if dual:
        e.set("dual", "dual")
    for extension in tokens[1:]:
        e=push_element(parent, EXTENSION, extension)
    return e

def push_section_heading(parent, level, text):
    e=push_element(parent, SECTION_HEADING, text)
    e.set("level", str(level))
    return e


# Inline Formatting and Mixed Content

"""Adds text at the end of an ET element. Handles mixed content
correctly, appending the argument text to argument element's text or
the tail of its last child, as necessary."""
def append_text_node(e, text):
    if len(e):
        if e[-1].tail:
            e[-1].tail+=text
        else:
            e[-1].tail=text
    else:
        if e.text:
            e.text+=text
        else:
            e.text=text

def parse_inlines(e):
    result=ET.Element(e.tag, attrib=e.attrib)
    if e.text:
        for n, l in enumerate(e.text.split("\n")):
            if n:
                append_text_node(result, "\n")
            mds=markdown.markdown(l, extensions=[FountainInlines()])
            if mds:
                # markdown returns mixed content wrapped in <p>
                p=ET.fromstring(mds.encode("utf-8"))
                if p.text:
                    append_text_node(result, p.text)
                result.extend(p)
            else:
                append_text_node(result, l)
    for child in e:
        result.append(parse_inlines(child))
        # if input has mixed content, parse child.tail; extend result
        # from p; child.tail=p.tail
    return result

"""Markdown extension that captures Fountain inline emphasis rules.
Fountain recognizes only underline, italic and bold inlines, and these
it calls out as such rather than generic "emphasis." This extension
removes all built-in Markdown patterms and installs Fountain-specific
ones."""
class FountainInlines(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.clear()
        md.inlinePatterns["escape"] = ip.EscapePattern(r'\\(.)', md)
        # stand-alone * or _
        md.inlinePatterns["not_em"] = ip.SimpleTextPattern(r'((^| )(\*|_)( |$))')
        # ***italic bold*** or ***italic*bold**
        md.inlinePatterns["b_i"]    = ip.DoubleTagPattern(r'(\*)\2{2}(.+?)\2(.*?)\2{2}', 'b,i')
        # ***bold**italic*
        md.inlinePatterns["i_b"]    = ip.DoubleTagPattern(r'(\*)\2{2}(.+?)\2{2}(.*?)\2', 'i,b')
        # **bold**
        md.inlinePatterns["b"]      = ip.SimpleTagPattern(r'(\*{2})(.+?)\2', 'b')
        # *italic*
        md.inlinePatterns["i"]      = ip.SimpleTagPattern(r'(\*)([^\*]+)\2', 'i')
        # _underline_
        md.inlinePatterns["u"]      = ip.SimpleTagPattern(r'(_)(.+?)\2', 'u')

# TODO: formatting: center
# TODO: formatting: lyrics
# TODO: reconstitute notes and clean up linefeeds around them
# TODO: reconstitute structure: sections
# TODO: reconstitute structure: scenes
# TODO: reconstitute structure: dialogue

def main(argv):
    print ET.tostring(parse(codecs.open(argv[1], encoding="utf-8")))

if __name__ == "__main__":
    main(sys.argv)
