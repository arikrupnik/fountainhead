# fountainhead.py: parses Fountain screenplays, outputs semantic XML

import sys
import re
import codecs
import xml.dom.minidom
import markdown
import markdown.inlinepatterns as ip
import argparse

# fountain source element types
TITLE_PAGE = "title-page"
TITLE_KEY = "key"
TITLE_VALUE = "value"

SCENE_HEADING = "scene-heading"
ACTION = "action"
CHARACTER = "character"
EXTENSION = "extension"         # the spec alludes to this without calling it an element
DIALOGUE = "line"               # the spec calls each line "dialogue;" fountainhead wraps each character's lines in <dialogue>
PARENTHETICAL = "parenthetical"
TRANSITION = "transition"
NOTE = "note"
BONEYARD = "boneyard"
SECTION_HEADING = "section-heading"
SYNOPSIS = "synopsis"
PAGE_BREAK = "page-break"


def parse_fountain(lines, flat_output):
    doc=xml.dom.minidom.getDOMImplementation().createDocument(None, "fountain", None)
    lines=map(lambda l: unicode(l.rstrip("\r\n"), "utf-8"), lines)
    title, body = split_title_body(lines)
    parse_title(title, doc.documentElement)
    body, notes = parse_comments_notes(body)
    pbody=parse_body(body, doc.documentElement)
    if flat_output:
        return doc
    structure_dialogue(doc)
    structure_scenes(doc)
    structure_sections(doc)
    parse_inlines(doc)
    reconstitute_notes(doc, notes)
    return doc

def split_title_body(lines):
    lines=discard_leading_empty_lines(lines)
    if not len(lines):
        # nothing at all
        return ((),())
    if (lines[0]!=lines[0].lstrip()) or \
       (not ":" in lines[0]) or \
       (re.search(r"[^\w ]", lines[0].split(":")[0])) or \
       (lines[0].strip().upper()=="FADE IN:") or \
       (lines[0].strip().upper().endswith(" TO:")):
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

def parse_title(lines, fountain):
    # "Information is encoding (sic) in the format key: value. Keys
    # can have spaces (e. g. Draft date), but must end with a colon."
    if lines:
        et=subElement(fountain, TITLE_PAGE)
        for l in lines:
            # "Values can be inline with the key or they can be
            # indented on a newline below the key (as shown with
            # Contact above). Indenting is 3 or more spaces, or a
            # tab. The indenting pattern allows multiple values for
            # the same key (multiple authors, multiple address
            # lines)."
            if l==l.lstrip():
                key, value=l.split(":", 1)
                ek=subElement(et, TITLE_KEY)
                ek.setAttribute("name", key)
                if value:
                    subElementWithText(ek, TITLE_VALUE, value.strip())
            else:
                subElementWithText(ek, TITLE_VALUE, l.strip())

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

def parse_body(lines, fountain):
    # this loop is a little awkward; it must accommodate fountain
    # requirements for lookback and lookahead ("A Scene Heading is any
    # line that has a blank line following it")
    if not len(lines):
        return
    line = lines[0]
    for nextline in lines[1:]:
        parse_line(line, fountain, nextline)
        line=nextline
    parse_line(line, fountain, None)

def parse_line(line, fountain, nextline):
    sline = line.strip()
    
    # first, I consider forcing elements
    
    # "Note that only a single leading period followed by an
    # alphanumeric character will force a Scene Heading. This allows
    # the writer to begin Action and Dialogue elements with ellipses
    # without worry that they'll be interpreted as Scene Headings."
    if sline.startswith(".") and not sline.startswith(".."):
        return push_scene_heading(fountain, sline[1:].lstrip())
    if sline.startswith("!"):
        return push_element(fountain, ACTION, sline[1:])
    if sline.startswith("@"):
        return push_character(fountain, sline[1:].lstrip())
    if sline.startswith(">") and not sline.endswith("<"):
        return push_element(fountain, TRANSITION, sline[1:].lstrip())

    # next, I handle context-free elements
    
    if sline.startswith("#"):
        # "If there are capturing groups in the separator and it
        # matches at the start of the string, the result will start
        # with an empty string."
        _,marker,text=re.split(r"(#{1,6})", sline, maxsplit=1)
        return push_section_heading(fountain, len(marker), text.strip())
    # page breaks may look like synopses, so I process them first
    if re.match(r"^===+$", sline):
        return push_element(fountain, PAGE_BREAK, "")
    if sline.startswith("="):
        return push_element(fountain, SYNOPSIS, sline[1:].lstrip())

    # next, elements that require lookahead or lookback
    
    # "A Scene Heading is any line that has a blank line following it,
    # and either begins with INT or EXT or similar (full list
    # below). A Scene Heading always has at least one blank line
    # preceding it."
    # "A line beginning with any of the following, followed by either a
    # dot or a space, is considered a Scene Heading (unless the line
    # is preceded by an exclamation point !). Case insensitive.
    # INT  EXT  EST  INT./EXT  INT/EXT  I/E"
    if last_line_empty(fountain):
        if not nextline:
            token = re.split(r"[\. ]", sline+" ")[0].upper()
            if token in ("INT", "EXT", "EST", "INT/EXT", "I/E"):
                return push_scene_heading(fountain, sline)
            if line.upper()==line:
                # "The requirements for Transition elements are:
                # Uppercase; Preceded by and followed by an empty
                # line; Ending in TO:"
                if line.endswith("TO:"):
                    return push_element(fountain, TRANSITION, sline)

    # "A Character element is any line entirely in uppercase, with one
    # empty line before it and without an empty line after it."
    if last_line_empty(fountain):
        if nextline:
            if line.upper()==line:
                # "Character names must include at least one
                # alphabetical character. "R2D2" works, but "23" does
                # not."
                if re.sub(r"[0-9_]", "", re.sub(r"\W", "", line)):
                    return push_character(fountain, sline)

    # "Dialogue is any text following a Character or Parenthetical
    # element." (really, any non-empty line -ak)
    # "Parentheticals follow a Character or Dialogue element, and are
    # wrapped in parentheses ()."
    if line and fountain.hasChildNodes() and fountain.lastChild.nodeName in (CHARACTER, EXTENSION, PARENTHETICAL, DIALOGUE):
        if re.match(r"^\(.*\)$", sline):
            return push_element(fountain, PARENTHETICAL, sline)
        else:
            return push_element(fountain, DIALOGUE, sline)
    
    # finally, "Action, or scene description, is any paragraph that
    # doesn't meet criteria for another element"
    return push_element(fountain, ACTION, line)

def last_line_empty(fountain):
    # assuming fountain is a flat list of elements, each containing a
    # single text node
    if not fountain.hasChildNodes():
        return True
    elif fountain.lastChild.tagName in (
            TITLE_PAGE, PAGE_BREAK, # first line on a page has no preceding line
            SYNOPSIS, SECTION_HEADING, # removing these leaves empty lines
            SCENE_HEADING, TRANSITION # require empty line in source, imply one in tree
    ):
        return True
    else:
        text=fountain.lastChild.lastChild.nodeValue
        return (not len(text)) or text.endswith("\n")

def push_element(fountain, tag, text):
    if tag in (ACTION, DIALOGUE) and fountain.hasChildNodes() and fountain.lastChild.nodeName==tag:
        # append line to multi-line elements
        fountain.lastChild.firstChild.nodeValue+="\n"+text
        e=fountain.lastChild
    else:
        if fountain.hasChildNodes():
            if fountain.lastChild.nodeName==ACTION:
                if not fountain.lastChild.lastChild.nodeValue:
                    # remove empty <action /> that comes from individual empty lines
                    fountain.removeChild(fountain.lastChild)
        e=subElementWithText(fountain, tag, text)
    return e

def push_scene_heading(parent, text):
    tokens=re.split(r"(#.*?#$)", text)
    if len(tokens)==1:
        e=push_element(parent, SCENE_HEADING, text)
    else:
        e=push_element(parent, SCENE_HEADING, tokens[0].strip())
        e.setAttribute("id", tokens[1].strip("#"))
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
        e.setAttribute("dual", "dual")
    for extension in tokens[1:]:
        subElementWithText(parent, EXTENSION, extension)
    return e

def push_section_heading(parent, level, text):
    tokens=re.split(r"(#.*?#$)", text)
    if len(tokens)==1:
        e=push_element(parent, SECTION_HEADING, text)
    else:
        e=push_element(parent, SECTION_HEADING, tokens[0].strip())
        e.setAttribute("id", tokens[1].strip("#"))
    e.setAttribute("level", str(level))
    return e

# Hierarchical Structures

def structure_dialogue(doc):
    for ch in doc.getElementsByTagName(CHARACTER):
        subElement(ch, "name").appendChild(ch.firstChild)
        # move extensions inside character
        n=ch.nextSibling
        while n and (n.nodeType!=n.ELEMENT_NODE or n.nodeName=="extension"):
            ch.appendChild(n)
            n=ch.nextSibling
        # move lines and parentheticals inside dialogue
        d=doc.createElement("dialogue")
        d.appendChild(ch.parentNode.replaceChild(d, ch))
        n=d.nextSibling
        while n and (n.nodeType!=n.ELEMENT_NODE or n.nodeName in (PARENTHETICAL,
                                                                     DIALOGUE)):
            d.appendChild(n)
            n=d.nextSibling
        # dual dialogue
        if ch.getAttribute("dual")=="dual":
            ch.removeAttribute("dual")
            dd=doc.createElement("dual-dialogue")
            dd.appendChild(d.parentNode.replaceChild(dd, d))
            if dd.previousSibling.nodeName=="dialogue":
                dd.insertBefore(dd.previousSibling, d)

def structure_scenes(doc):
    for sh in doc.getElementsByTagName(SCENE_HEADING):
        s=doc.createElement("scene")
        s.appendChild(sh.parentNode.replaceChild(s, sh))
        id=sh.getAttribute("id")
        if id:
            sh.removeAttribute("id")
            s.setAttribute("id", id)
        n=s.nextSibling
        while n and (n.nodeType!=n.ELEMENT_NODE or n.nodeName in (SYNOPSIS,
                                                                  NOTE,
                                                                  ACTION,
                                                                  "dialogue",
                                                                  "dual-dialogue")):
            s.appendChild(n)
            n=s.nextSibling

def structure_sections(doc):
    max_level=0
    for sh in doc.getElementsByTagName(SECTION_HEADING):
        max_level=max(max_level, int(sh.getAttribute("level")))
    for level in range(1, max_level+1):
        for sh in doc.getElementsByTagName(SECTION_HEADING):
            if int(sh.getAttribute("level"))==level:
                s=doc.createElement("section")
                s.setAttribute("heading", sh.parentNode.replaceChild(s, sh).firstChild.nodeValue)
                id=sh.getAttribute("id")
                if id:
                    s.setAttribute("id", id)
                n=s.nextSibling
                while n and (n.nodeType!=n.ELEMENT_NODE or n.nodeName not in (PAGE_BREAK)):
                    if n.nodeName==SECTION_HEADING and int(n.getAttribute("level"))<=level:
                        break
                    s.appendChild(n)
                    n=s.nextSibling

# Inline Formatting and Mixed Content

def parse_inlines(doc):
    # assuming these have text-only content at this point
    m=markdown.Markdown(extensions=[FountainInlines()])
    for tag in (TITLE_VALUE, ACTION, DIALOGUE):
        for e in doc.getElementsByTagName(tag):
            text=e.removeChild(e.firstChild).nodeValue
            for n, l in enumerate(text.strip().split("\n")):
                if n:
                    appendText(e, "\n")
                mds=m.convert(l)
                if mds:
                    p=xml.dom.minidom.parseString(mds.encode("utf-8")).documentElement
                    c=p.firstChild
                    while c:
                        e.appendChild(c)
                        c=p.firstChild

"""Markdown extension that captures Fountain inline emphasis rules.
Fountain recognizes only underline, italic and bold inlines, and these
it calls out as such rather than generic "emphasis." This extension
removes all built-in Markdown patterms and installs Fountain-specific
ones."""
class FountainInlines(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        # I use Makrdown to parse inline formatting in individual
        # lines of text; block structure I handle in parse_line()
        # above. Unless this strategy changes, none of the block
        # processors are useful except ParagraphProcessor which wraps
        # mixed content in <p>'s. Many actively interfere with
        # Fountain syntax, e.g., BlockQuoteProcessor replaces
        # '>center<' with <blockquote>center&lt;</blocquote>
        md.parser.blockprocessors.clear()
        md.parser.blockprocessors["paragraph"]=\
            markdown.blockprocessors.ParagraphProcessor(md.parser)

        # I use the markdown mechanism for inlinePatterns, but replace
        # all built-in patterns. Some markdown patterns look similar
        # to Fountain but aren't: e.g., Fountain differentiates
        # between *italic* and _underline_
        md.inlinePatterns.clear()
        md.inlinePatterns["escape"] = ip.EscapePattern(r'\\(.)', md)
        md.inlinePatterns["center"] = ip.SimpleTagPattern(r'(^\s*>\s*)(.+?)(\s*<\s*$)', "center")
        md.inlinePatterns["lyric"]  = ip.SimpleTagPattern(r'(^~)(.+?)($)', "lyric")
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
        
        # not strictly speaking formatting, but these are inline
        md.inlinePatterns["note"]   = ip.SimpleTagPattern(r'(\n?\[\[)(.+?)(\]\]\n?)', 'note')


def reconstitute_notes(doc, notes):
    for n in doc.getElementsByTagName("note"):
        appendText(n, notes[int(n.removeChild(n.firstChild).nodeValue)])
    # TODO: "The empty lines around the Note on its own line would be removed in parsing."

# DOM utilities

# This is part of DOM Level 1, but apparently has quirks in minidom
def ownerDocument(node):
    if node.nodeType==node.DOCUMENT_NODE:
        return node
    else:
        return ownerDocument(node.parentNode)

def subElement(e, tagName):
    return e.appendChild(ownerDocument(e).createElement(tagName))

def appendText(e, text):
    return e.appendChild(ownerDocument(e).createTextNode(text))

def subElementWithText(e, tagName, text):
    e=subElement(e, tagName)
    appendText(e, text)
    return e

def main(argv):
    ap=argparse.ArgumentParser(description="Convert Fountain input to XML.")
    ap.add_argument("-f", "--flatoutput",
                    action="store_true",
                    help="output flat XML without hierarchical structure")
    ap.add_argument("infile", metavar="file.fountain", nargs="?",
                    type=argparse.FileType("r"),
                    default=sys.stdin)
    args=ap.parse_args()
    print codecs.encode(parse_fountain(args.infile, args.flatoutput).toxml(), "utf-8")

if __name__ == "__main__":
    main(sys.argv)
