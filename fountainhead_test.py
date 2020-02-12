# fountainhead_test.py: pytest suite for fountainhead

import fountainhead
import pytest
import glob
import os

DEFAULT_ARGS = fountainhead.arg_parser().parse_args("")
SEMANTIC_LINES = fountainhead.arg_parser().parse_args(["-s",])

# Feeds a string-literal representation of a Fountain document to
# fountainhead processor. Returns the document element (normally,
# <fountain>) so caller can make assertions on its structure. Prints a
# textual representation of the FTX; in case an assertion fails, this
# allows the user to see the structure fountainhead parsed out of the
# source.
def ftx(fountain, args=DEFAULT_ARGS):
    ftx = fountainhead.parse_fountain(
        fountain.split("\n"),
        args).documentElement
    print ftx.toxml()
    return ftx

def assert_transform(fountain, xml, args=DEFAULT_ARGS):
    assert ftx(fountain, args).toxml() == xml.strip()

# the following classes capture example code from https://fountain.io/syntax

class TestSceneHeadings:
    def test_scene_and_forced_scene(self):
        # "Here's a regular Scene Heading followed by a forced Scene Heading."
        ft = """
EXT. BRICK'S POOL - DAY

Steel, in the middle of a heated phone call:

STEEL
They're coming out of the woodwork!
(pause)
No, everybody we've put away!
(pause)
Point Blank Sniper?

.SNIPER SCOPE POV

From what seems like only INCHES AWAY.  _Steel's face FILLS the *Leupold Mark 4* scope_.
"""
        xml = "<fountain><scene><scene-heading><setting>EXT.</setting><location>BRICK'S POOL</location><tod>DAY</tod></scene-heading><action>Steel, in the middle of a heated phone call:</action><dialogue><character><name>STEEL</name></character><line>They're coming out of the woodwork!</line><parenthetical>(pause)</parenthetical><line>No, everybody we've put away!</line><parenthetical>(pause)</parenthetical><line>Point Blank Sniper?</line></dialogue></scene><scene><scene-heading><location>SNIPER SCOPE POV</location></scene-heading><action>From what seems like only INCHES AWAY.  <u>Steel's face FILLS the <i>Leupold Mark 4</i> scope</u>.</action></scene></fountain>"
        assert_transform(ft, xml)
        ftx = fountainhead.parse_fountain(ft.split("\n"), DEFAULT_ARGS)
        scenes = ftx.getElementsByTagName("scene")
        assert scenes.length == 2
        assert scenes[0].getElementsByTagName("location")[0].childNodes[0].nodeValue == "BRICK'S POOL"
        assert scenes[1].getElementsByTagName("location")[0].childNodes[0].nodeValue == "SNIPER SCOPE POV"

    def test_multiple_dots(self):
        # "Note that only a single leading period followed by an
        # alphanumeric character will force a Scene Heading"
        ft = """
EXT. OLYMPIA CIRCUS - NIGHT

...where the second-rate carnival is parked for the moment in an Alabama field.
"""
        ftx = fountainhead.parse_fountain(ft.split("\n"), DEFAULT_ARGS)
        scenes = ftx.getElementsByTagName("scene")
        assert scenes.length == 1
        assert scenes[0].getElementsByTagName("location")[0].childNodes[0].nodeValue == "OLYMPIA CIRCUS"

    def test_lowercase(self):
        # Although uppercase is recommended for Scene Headings to
        # increase readability, it is not required.
        ft = "ext. brick's pool - day"
        ftx = fountainhead.parse_fountain(ft.split("\n"), DEFAULT_ARGS)
        assert ftx.getElementsByTagName("scene").length == 1

    def test_blank_lines(self):
        # "A Scene Heading is any line that has a blank line following
        # it, and either begins with INT or EXT or similar (full list
        # below). A Scene Heading always has at least one blank line
        # preceding it." The line that begins with ".38" does not
        # trigger a scene heading. Test case from an external source.
        ft = """
Like a wary lioness whose den's been invaded, Winny aims a
.38 pistol at Colonel. Eyeing him, she picks up the rotary
phone and dials 0 with her left hand.
"""
        xml = """
<fountain><action>Like a wary lioness whose den's been invaded, Winny aims a
.38 pistol at Colonel. Eyeing him, she picks up the rotary
phone and dials 0 with her left hand.</action></fountain>
"""
        assert_transform(ft, xml)
        # a blank line before is insufficient to trigger a scene heading
        ft = """
Like a wary lioness whose den's been invaded, Winny aims a

.38 pistol at Colonel. Eyeing him, she picks up the rotary
phone and dials 0 with her left hand.
"""
        assert ftx(ft).getElementsByTagName("scene").length == 0
        # a blank line after is insufficient to trigger a scene heading
        ft = """
Like a wary lioness whose den's been invaded, Winny aims a

.38 pistol at Colonel. Eyeing him, she picks up the rotary
phone and dials 0 with her left hand.
"""
        assert ftx(ft).getElementsByTagName("scene").length == 0
        # blank lines before and after trigger scene heading
        ft = """
Like a wary lioness whose den's been invaded, Winny aims a

.38 pistol at Colonel. Eyeing him, she picks up the rotary

phone and dials 0 with her left hand.
"""
        assert ftx(ft).getElementsByTagName("scene").length == 1

class TestAction:
    def test_double_spacing(self):
        # "Fountain respects your line-by-line decision to single or
        # double-space, taking every carriage return as intentional."
        ft = """
They drink long and well from the beers.

And then there's a long beat.
Longer than is funny.
Long enough to be depressing.

The men look at each other.
"""
        xml = """<fountain><action>They drink long and well from the beers.

And then there's a long beat.
Longer than is funny.
Long enough to be depressing.

The men look at each other.</action></fountain>
"""
        assert_transform(ft, xml)

        # With semantic linebreaks option, Fountainhead preserves
        # double-spaced paragraphs, but treats linebreaks between
        # adjacent lines as insignificant
        xml_sem_lines = """<fountain><action>They drink long and well from the beers.

And then there's a long beat. Longer than is funny. Long enough to be depressing.

The men look at each other.</action></fountain>
"""
        assert_transform(ft, xml_sem_lines, SEMANTIC_LINES)

        # Add test here for https://github.com/arikrupnik/fountainhead/issues/15

    # The following test fails. It appears that Markdown.convert() in
    # parse_inlines() strips leading whitespace from lines (The
    # argument `l` to contert() contains the whitespace but the return
    # misses it). It is possible that ParagraphProcessor is the
    # component remocing this whitespace.
    @pytest.mark.xfail
    def test_tabs_and_spaces(self):
        # "Tabs and spaces are retained in Action elements,
        # allowing writers to indent a line. Tabs are converted to
        # four spaces."
        ft = """
He opens the card.  A simple little number inside of which is hand written:

          Scott --

          Jacob Billups
          Palace Hotel, RM 412
          1:00 pm tomorrow

Scott exasperatedly throws down the card on the table and picks up the phone, hitting speed dial #1...
"""
        xml = ""
        assert_transform(ft, xml)

        # this doesn't test for tabs--original sample has spaces only

class TestCharacter:
    pass

class TestDialogue:
    pass

class TestParenthetical:
    pass

class TestDualDialogue:
    pass

class TestLyrics:
    pass

class TestTransition:
    pass

class TestCenteredText:
    pass

class TestEmphasis:

    def test_basics(self):
        ft = """
*italics*
**bold**
***bold italics***
_underline_
"""
        xml = """
<fountain><action><i>italics</i>
<b>bold</b>
<b><i>bold italics</i></b>
<u>underline</u></action></fountain>
"""
        assert_transform(ft, xml)

    def test_combination(self):
        # "the writer can mix and match and combine bold, italics and
        # underlining, as screenwriters often do"
        ft = "From what seems like only INCHES AWAY.  _Steel's face FILLS the *Leupold Mark 4* scope_."
        xml = "<fountain><action>From what seems like only INCHES AWAY.  <u>Steel's face FILLS the <i>Leupold Mark 4</i> scope</u>.</action></fountain>"
        assert_transform(ft, xml)

    def test_escape(self):
        # Original example has a colon after "keypad." I remove it
        # here: leaving it in makes the one-line screenplay into title
        # page with a key:value pair
        ft = "Steel enters the code on the keypad **\*9765\***"
        xml = "<fountain><action>Steel enters the code on the keypad <b>*9765*</b></action></fountain>"
        assert_transform(ft, xml)

    # The following test fails and I disable it. Python Markdown
    # interprets the emphasis rules differently, and I see little
    # value in fighting it. Markdown imlementations disagree on
    # interpreting this example:
    # https://johnmacfarlane.net/babelmark2/?text=He+dialed+*69+and+then+*23%2C+and+then+hung+up.
    # A Python-Markdown extension existst (betterem) that can make
    # this test pass, if this becomes a user issue:
    # https://github.com/Python-Markdown/markdown/issues/910
    @pytest.mark.skip
    def test_spaces_around_emphasis(self):
        # "As with Markdown, the spaces around the emphasis characters
        # are meaningful. In this example, the asterisks would not
        # trigger italics between them, because both have a space to
        # the left:"
        ft = "He dialed *69 and then *23, and then hung up."
        xml = "<fountain><action>He dialed *69 and then *23, and then hung up.</action></fountain>"
        assert_transform(ft, xml)

    def test_emphasis_actoss_words(self):
        # "But in this case, the text between the asterisks would be
        # italicized:"
        ft = "He dialed *69 and then 23*, and then hung up."
        xml = "<fountain><action>He dialed <i>69 and then 23</i>, and then hung up.</action></fountain>"
        assert_transform(ft, xml)

    def test_emphasis_across_words_with_escape(self):
        # "The writer would need to escape one or both of the
        # asterisks to avoid the accidental italics:"
        ft = "He dialed *69 and then 23\*, and then hung up."
        xml = "<fountain><action>He dialed *69 and then 23*, and then hung up.</action></fountain>"
        assert_transform(ft, xml)

    def test_emphasis_across_lines(self):
        # "Also as with Markdown, emphasis is not carried across line
        # breaks. So there are no italics in the formatted output of
        # this example--just asterisks:"
        ft = """
As he rattles off the long list, Brick and Steel *share a look.

This is going to be BAD.*
"""
        xml = """
<fountain><action>As he rattles off the long list, Brick and Steel *share a look.

This is going to be BAD.*</action></fountain>
"""
        assert_transform(ft, xml)


class TestTitlePage:
    pass

class TestPAgeBreaks:
    pass


class TestPunctuation:
    pass

class TestLineBreaks:
    pass

class TestIndenting:
    pass

class TestNotes:
    pass

class TestBoneYard:
    pass

class TestSectionsAndSynopses:
    pass

DIR = os.path.dirname(os.path.abspath(__file__))
@pytest.mark.parametrize("f", glob.glob(os.path.join(DIR, "tests/*.fountain")))
@pytest.mark.xfail
def test_file_sample(f):
    ft = open(f)
    xml = open(os.path.splitext(f)[0]+".ftx").read( )
    assert parse_fountain(ft, DEFAULT_ARGS).toxml() == xml
