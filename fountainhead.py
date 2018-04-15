# fountainhead.py: parses Fountain screenplays, outputs semantic XML

import sys
import re
import codecs
import xml.dom.minidom
import markdown
import markdown.inlinepatterns as ip
import argparse
import os.path

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

INCLUDE = "include"


def parse_fountain(lines, args):
    doc=xml.dom.minidom.getDOMImplementation().createDocument(None, "fountain", None)
    if args.css:
        doc.insertBefore(doc.createProcessingInstruction("xml-stylesheet", "href='%s'" % args.css),
                         doc.documentElement)
    lines=map(lambda l: unicode(l.rstrip("\r\n"), "utf-8"), lines)
    title, body = split_title_body(lines)
    parse_title(title, doc.documentElement, args.meta)
    body, notes = parse_comments_notes(body)
    pbody=parse_body(body, doc.documentElement, args.syntax_extensions)
    if args.flat_output:
        return doc
    structure_dialogue(doc)
    structure_scenes(doc)
    structure_sections(doc)
    parse_inlines(doc, args.semantic_linebreaks)
    reconstitute_notes(doc, notes)
    if args.syntax_extensions:
        process_includes(doc, args)
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

def parse_title(lines, fountain, extra_keys):
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
        # additional keys can come from command-line arguments, but
        # only if the document already contains its own metadata
        if extra_keys:
            for meta in extra_keys:
                key, value=meta
                if key and value:
                    ek=subElement(et, TITLE_KEY)
                    ek.setAttribute("name", key)
                    subElementWithText(ek, TITLE_VALUE, value)

def parse_comments_notes(lines):
    text="\n".join(lines)
    text=re.sub(r"(/\*.*?\*/)", "", text, flags=re.DOTALL)
    out_text=""
    notes=[]
    for token in re.split(r"(\[\[.*?\]\])", text, flags=re.DOTALL):
        if token.startswith("[[") and token.endswith("]]"):
            out_text+="[["+str(len(notes))+"]]"
            notes+=[token[2:-2]]
        else:
            out_text+=token
    return out_text.split("\n"), notes

# Parsing lines of text into text-only elements

def parse_body(lines, fountain, syntax_extensions):
    # this loop is a little awkward; it must accommodate fountain
    # requirements for lookback and lookahead ("A Scene Heading is any
    # line that has a blank line following it")
    if not len(lines):
        return
    line = lines[0]
    for nextline in lines[1:]:
        parse_line(line, fountain, nextline, syntax_extensions)
        line=nextline
    parse_line(line, fountain, None, syntax_extensions)

def parse_line(line, fountain, nextline, syntax_extensions):
    sline = line.strip()
    
    # first, I consider forcing elements
    if sline.startswith("!"):
        return push_element(fountain, ACTION, sline[1:])

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
    # FountainHead extensions piggyback on synopsis
    if syntax_extensions:
        if sline.startswith("=<"):
            return push_element(fountain, INCLUDE, sline[2:])
    # regular synopsis
    if sline.startswith("="):
        return push_element(fountain, SYNOPSIS, sline[1:].lstrip())

    # next, elements that require lookahead or lookback
    if last_line_empty(fountain):
        if not nextline:
            # "A Scene Heading is any line that has a blank line
            # following it, and either begins with INT or EXT or
            # similar (full list below). A Scene Heading always has at
            # least one blank line preceding it."
            # "A line beginning with any of the following, followed by
            # either a dot or a space, is considered a Scene Heading
            # (unless the line is preceded by an exclamation point
            # !). Case insensitive.  INT EXT EST INT./EXT INT/EXT I/E"
            token = re.split(r"[\. ]", sline+" ")[0].upper()
            if token in ("INT", "EXT", "EST", "INT/EXT", "I/E"):
                return push_scene_heading(fountain,
                                          sline[len(token)+1:].lstrip(),
                                          setting=sline[:len(token)+1].rstrip())
            # "You can "force" a Scene Heading by starting the line
            # with a single period. Note that only a single leading
            # period followed by an alphanumeric character will force
            # a Scene Heading. This allows the writer to begin Action
            # and Dialogue elements with ellipses without worry that
            # they'll be interpreted as Scene Headings."
            if sline.startswith(".") and not sline.startswith(".."):
                return push_scene_heading(fountain, sline[1:].lstrip())

            # "The requirements for Transition elements are:
            # Uppercase; Preceded by and followed by an empty line;
            # Ending in TO:"
            if line.upper()==line:
                if line.endswith("TO:"):
                    return push_element(fountain, TRANSITION, sline)
            # "You can force any line to be a transition by beginning
            # it with a greater-than symbol >."
            if sline.startswith(">") and not sline.endswith("<"):
                return push_element(fountain, TRANSITION, sline[1:].lstrip())

    if last_line_empty(fountain):
        if nextline:
            # "A Character element is any line entirely in uppercase,
            # with one empty line before it and without an empty line
            # after it."
            if line.upper()==line:
                # "Character names must include at least one
                # alphabetical character. "R2D2" works, but "23" does
                # not."
                if re.sub(r"[0-9_]", "", re.sub(r"\W", "", line)):
                    return push_character(fountain, sline)
            # "You can force a Character element by preceding it with
            # the "at" symbol @."
            if sline.startswith("@"):
                return push_character(fountain, sline[1:].lstrip())

    # "Dialogue is any text following a Character or Parenthetical
    # element."
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

def push_scene_heading(parent, text, setting=None):
    tokens=re.split(r"(#.*?#$)", text)
    if len(tokens)==1:
        id=None
    else:
        text=tokens[0].strip()
        id=tokens[1].strip("#")

    tokens=text.rsplit("-", 1)
    if len(tokens)==1:
        tod=None
    else:
        text=tokens[0].rstrip(" -")
        tod=tokens[1].lstrip(" -")

    e=push_element(parent, SCENE_HEADING, text)
    if setting:
        e.setAttribute("setting", setting)
    if id:
        e.setAttribute("id", id)
    if tod:
        e.setAttribute("tod", tod)
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

        # move @id up to scene
        id=sh.getAttribute("id")
        if id:
            sh.removeAttribute("id")
            s.setAttribute("id", id)

        # move text to <location>
        subElement(sh, "location").appendChild(sh.firstChild)

        # move @setting and @tod to elements
        setting=sh.getAttribute("setting")
        if setting:
            sh.removeAttribute("setting")
            se=subElementWithText(sh, "setting", setting)
            sh.insertBefore(se, sh.firstChild)

        tod=sh.getAttribute("tod")
        if tod:
            sh.removeAttribute("tod")
            te=subElementWithText(sh, "tod", tod)

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
                s.setAttribute("heading",
                               sh.parentNode.replaceChild(s, sh).firstChild.nodeValue)
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

def parse_inlines(doc, semantic_linebreaks):
    # assuming these have text-only content at this point
    m=markdown.Markdown(extensions=[FountainInlines()])
    for tag in (TITLE_VALUE, ACTION, DIALOGUE):
        for e in doc.getElementsByTagName(tag):
            text=e.removeChild(e.firstChild).nodeValue
            if semantic_linebreaks:
                # consolidate adjacent lines; leave as is if blank
                # lines intervene
                text=re.sub(r"([^\n])\n([^\n])", r"\1 \2", text)
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
removes all built-in Markdown patterns and installs Fountain-specific
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
        md.inlinePatterns["note"]   = ip.SimpleTagPattern(r'(\[\[)(.+?)(\]\])', 'note')


def reconstitute_notes(doc, notes):
    for n in doc.getElementsByTagName(NOTE):
        appendText(n, notes[int(n.removeChild(n.firstChild).nodeValue)])

    # "The empty lines around the Note on its own line would be removed in parsing."
    line_notes=[]
    for n in doc.getElementsByTagName(NOTE):
        n.parentNode.normalize()
        ps=n.previousSibling
        ns=n.nextSibling
        if ps and ns:
            if ps.nodeType==n.TEXT_NODE and ns.nodeType==n.TEXT_NODE:
                if ps.nodeValue.endswith("\n") and ns.nodeValue.startswith("\n"):
                    line_notes+=[n]
    for n in line_notes:
        # remove all linefeeds before
        ps=n.previousSibling
        if ps and ps.nodeType==n.TEXT_NODE and ps.nodeValue.endswith("\n"):
            ptext=ps.nodeValue.rstrip("\n")
            if ptext:
                n.parentNode.replaceChild(
                    doc.createTextNode(ptext),
                    ps)
            else:
                n.parentNode.removeChild(ps)
        ns=n.nextSibling
        if ns and ns.nodeType==n.TEXT_NODE and ns.nodeValue.startswith("\n"):
            # leave one linefeed after, (if next element is also a
            # <note>, it removes this linefeed in its turn)
            n.parentNode.replaceChild(
                doc.createTextNode("\n"+ns.nodeValue.lstrip("\n")),
                ns)

def filename_fragment(filename, infilename):
    tokens=filename.rsplit("#", 1)
    name=tokens[0]
    if os.path.exists(infilename):
        name=os.path.join(os.path.dirname(infilename), name)
    fragment=len(tokens)==2 and tokens[1] or None
    return name, fragment

def process_includes(doc, args):
    for i in doc.getElementsByTagName(INCLUDE):
        filename, fragment_id=filename_fragment(i.firstChild.nodeValue, args.infile.name)
        try:
            f=open(filename)
        except IOError as e:
            # "Fountain does its best to sensibly interpret the text file
            # into screenplay formatting. When in doubt, Fountain returns
            # text as Action."
            a=doc.createElement(ACTION)
            a.appendChild(doc.createTextNode(filename + ": " + e.strerror))
            i.parentNode.replaceChild(a, i)
            return
        child_doc=parse_fountain(f, args)
        fragment=fragment_id and findElementByAttributeValue(child_doc, "id", fragment_id)
        if fragment:
            i.parentNode.replaceChild(fragment, i)
        else:
            e = child_doc.documentElement.firstChild
            while e:
                e.parentNode.removeChild(e)
                if e.nodeName!=TITLE_PAGE:
                    i.parentNode.insertBefore(e, i)
                e = child_doc.documentElement.firstChild
            i.parentNode.removeChild(i)

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

def findElementByAttributeValue(n, attr, value):
    for e in n.getElementsByTagName("*"):
        if e.getAttributeNode(attr) and e.getAttribute(attr)==value:
            return e


# Dependencies

def find_dependencies(infile):
    deps=set()
    for l in infile:
        # consider abstracting .rstrip("\r\n"), etc. into a function
        # that both find_dependencies and parse_fountain can use
        if l.startswith("=<"):
            f,_=filename_fragment(l[2:].rstrip("\r\n"), infile.name)
            deps.add(f)
            try:
                i=open(f)
                deps |= find_dependencies(i)
            except IOError:
                pass
    return deps

def make_rule(args):
    target_filename=os.path.splitext(args.infile.name)[0]+".ftx"
    deps=find_dependencies(args.infile)
    if deps:
        return target_filename + ": " + " ".join(deps)
    else:
        return ""

def main(argv):
    ap=argparse.ArgumentParser(description="Convert Fountain input to XML.")
    ap.add_argument("-s", "--semantic-linebreaks",
                    action="store_true",
                    help="treat single line breaks as space characters")
    ap.add_argument("-c", "--css",
                    metavar="uri",
                    help="use this CSS stylesheet")
    ap.add_argument("-f", "--flat-output",
                    action="store_true",
                    help="output flat XML without hierarchical structure")
    ap.add_argument("-m", "--meta",
                    action="append", nargs=2, metavar=("key", "value"),
                    help="add metadata values to title page")
    ap.add_argument("-x", "--syntax-extensions",
                    action="store_true",
                    help="interpert =<include.fountain fountainhead extexsion")
    ap.add_argument("-M", "--dependencies",
                    action="store_true",
                    help="output a make(1) rule describing the dependencies for this file")
    ap.add_argument("infile", metavar="file.fountain", nargs="?",
                    type=argparse.FileType("r"),
                    default=sys.stdin)
    args=ap.parse_args()

    if args.dependencies:
        print make_rule(args)
    else:
        print codecs.encode(parse_fountain(args.infile, args).toxml(), "utf-8")

if __name__ == "__main__":
    main(sys.argv)
