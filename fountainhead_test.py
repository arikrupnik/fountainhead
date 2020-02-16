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
    print fountainhead.pprint(ftx)
    return ftx

def assert_transform(fountain, xml, args=DEFAULT_ARGS):
    assert fountainhead.pprint(ftx(fountain, args)).strip() == xml.strip()

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
        xml = """
<fountain>
  <scene>
    <scene-heading><setting>EXT.</setting><location>BRICK'S POOL</location><tod>DAY</tod></scene-heading>
    <action>Steel, in the middle of a heated phone call:</action>
    <dialogue>
      <character><name>STEEL</name></character>
      <line>They're coming out of the woodwork!</line>
      <parenthetical>(pause)</parenthetical>
      <line>No, everybody we've put away!</line>
      <parenthetical>(pause)</parenthetical>
      <line>Point Blank Sniper?</line>
    </dialogue>
  </scene>
  <scene>
    <scene-heading><location>SNIPER SCOPE POV</location></scene-heading>
    <action>From what seems like only INCHES AWAY.  <u>Steel's face FILLS the <i>Leupold Mark 4</i> scope</u>.</action>
  </scene>
</fountain>
"""
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
<fountain>
  <action>Like a wary lioness whose den's been invaded, Winny aims a
.38 pistol at Colonel. Eyeing him, she picks up the rotary
phone and dials 0 with her left hand.</action>
</fountain>
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
        xml = """
<fountain>
  <action>They drink long and well from the beers.

And then there's a long beat.
Longer than is funny.
Long enough to be depressing.

The men look at each other.</action>
</fountain>
"""
        assert_transform(ft, xml)

        # With semantic linebreaks option, Fountainhead preserves
        # double-spaced paragraphs, but treats linebreaks between
        # adjacent lines as insignificant
        xml_sem_lines = """
<fountain>
  <action>They drink long and well from the beers.

And then there's a long beat. Longer than is funny. Long enough to be depressing.

The men look at each other.</action>
</fountain>
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
        xml = """
<fountain>
  <action>He opens the card.  A simple little number inside of which is hand written:

          Scott --

          Jacob Billups
          Palace Hotel, RM 412
          1:00 pm tomorrow

Scott exasperatedly throws down the card on the table and picks up the phone, hitting speed dial #1...</action>
</fountain>
"""
        assert_transform(ft, xml)

        # this doesn't test for tabs--original sample has spaces only

class TestCharacter:
    # "A Character element is any line entirely in uppercase, with one
    # empty line before it and without an empty line after it."
    def test_basics(self):
        # This is the example that appears in the spec. It does not
        # have an empty line before it, but it is the first thing in
        # the screenplay
        ft = """STEEL
The man's a myth!"""
        xml = """
<fountain>
  <dialogue>
    <character><name>STEEL</name></character>
    <line>The man's a myth!</line>
  </dialogue>
</fountain>
"""
        assert_transform(ft, xml)
        # "If you want to indent a Character element with tabs or
        # spaces, you can, but it is not necessary."
        assert_transform("    "+ft, xml)
    def test_basics_with_preceding_elements(self):
        ft = """
trailing text.

STEEL
The man's a myth!"""
        assert ftx(ft).getElementsByTagName("dialogue").length == 1
    def test_basics_without_preceding_empty_line(self):
        ft = """
trailing text.
STEEL
The man's a myth!"""
        assert ftx(ft).getElementsByTagName("dialogue").length == 0
    def test_basics_with_following_empty_line(self):
        ft = """
trailing text.

STEEL

The man's a myth!"""
        assert ftx(ft).getElementsByTagName("dialogue").length == 0

    # This fails. Fountainhead takes the preceding stipulation, "A
    # Character element is any line entirely in uppercase..."
    # literally. So "MOM (O. S.)" parses as a character line, but
    # "HANS (on the radio)" parses as a line of action.
    @pytest.mark.xfail
    def test_character_extensions(self):
        # "'Character Extensions'--the parenthetical notations that
        # follow a character name on the same line--may be in
        # uppercase or lowercase"
        ft = """
MOM (O. S.)
Luke! Come down for supper!

HANS (on the radio)
What was it you said?
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>MOM</name><extension>(O. S.)</extension></character>
    <line>Luke! Come down for supper!</line>
  </dialogue>
  <dialogue>
    <character><name>HANS</name><extension>(on the radio)</extension></character>
    <line>What was it you said?</line>
  </dialogue>
</fountain>
"""
        assert_transform(ft, xml)

    def test_character_name_rules(self):
        # "Character names must include at least one alphabetical
        # character. "R2D2" works, but "23" does not."
        ft = """
R2D2
Beep!

23
Blop!
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>R2D2</name></character>
    <line>Beep!</line>
  </dialogue>
  <action>23
Blop!</action>
</fountain>
"""
        assert_transform(ft, xml)

    def test_force_character(self):
        # "You can force a Character element by preceding it with the
        # "at" symbol @."
        ft = """
@McCLANE
Yippie ki-yay! I got my lower-case C back!
"""
        assert ftx(ft).getElementsByTagName("character").length == 1
        # removing @ makes action out of McCLANE
        assert ftx(ft.replace("@", "")).getElementsByTagName("character").length == 0

class TestDialogue:
    def test_basics(self):
        # "Dialogue is any text following a Character or Parenthetical
        # element."
        ft = """
SANBORN
A good 'ole boy. You know, loves the Army, blood runs green. Country boy. Seems solid.
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>SANBORN</name></character>
    <line>A good 'ole boy. You know, loves the Army, blood runs green. Country boy. Seems solid.</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)

    def test_line_breaks(self):
        # "Manual line breaks are allowed in Dialogue"
        ft = """DAN
Then let's retire them. 
_Permanently_.
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>DAN</name></character>
    <line>Then let's retire them.
<u>Permanently</u>.</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)
        # but with semantic linbreaks option, Fountainhead folds adjacent lines
        xml = """
<fountain>
  <dialogue>
    <character><name>DAN</name></character>
    <line>Then let's retire them. <u>Permanently</u>.</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml, SEMANTIC_LINES)

class TestParenthetical:
    def test_basics(self):
        ft = """
STEEL
(starting the engine)
So much for retirement!
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>STEEL</name></character>
    <parenthetical>(starting the engine)</parenthetical>
    <line>So much for retirement!</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)

class TestDualDialogue:
    def test_dd(self):
        ft = """
BRICK
Screw retirement.

STEEL ^
Screw retirement.
"""
        xml = """
<fountain>
  <dual-dialogue>
    <dialogue>
      <character><name>BRICK</name></character>
      <line>Screw retirement.</line>
    </dialogue>
    <dialogue>
      <character><name>STEEL</name></character>
      <line>Screw retirement.</line>
    </dialogue>
  </dual-dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)

class TestLyrics:
    def test_lyrics(self):
        ft = """
~Willy Wonka! Willy Wonka! The amazing chocolatier!
~Willy Wonka! Willy Wonka! Everybody give a cheer!
"""
        xml = """
<fountain>
  <action><lyric>Willy Wonka! Willy Wonka! The amazing chocolatier!</lyric>
<lyric>Willy Wonka! Willy Wonka! Everybody give a cheer!</lyric></action>
</fountain>
"""
        # what is the source of the newline between <lyric>s?
        assert_transform(ft, xml)

class TestTransition:
    def test_transition(self):
        ft = """
Jack begins to argue vociferously in Vietnamese (?), But mercifully we...

CUT TO:

EXT. BRICK'S POOL - DAY"""
        xml = """
<fountain>
  <action>Jack begins to argue vociferously in Vietnamese (?), But mercifully we...</action>
  <transition>CUT TO:</transition>
  <scene>
    <scene-heading><setting>EXT.</setting><location>BRICK'S POOL</location><tod>DAY</tod></scene-heading>
  </scene>
</fountain>
"""
        assert_transform(ft, xml)
    def test_force_transition(self):
        ft = """
Brick and Steel regard one another.  A job well done.

> Burn to White."""
        xml = """
<fountain>
  <action>Brick and Steel regard one another.  A job well done.</action>
  <transition>Burn to White.</transition>
</fountain>
"""
        assert_transform(ft, xml)

class TestCenteredText:
    def test_ct(self):
        # "Centered text constitutes an Action element, and is
        # bracketed with greater/less-than:"
        ft = ">THE END<"
        xml = """
<fountain>
  <action><center>THE END</center></action>
</fountain>
"""
        assert_transform(ft, xml)
    def test_ct_whitespace(self):
        # "Leading spaces are usually preserved in Action, but not for
        # centered text, so you can add spaces between the text and
        # the >< if you like."
        ft = "> THE END <"
        xml = """
<fountain>
  <action><center>THE END</center></action>
</fountain>"""
        assert_transform(ft, xml)

class TestEmphasis:

    def test_basics(self):
        ft = """
*italics*
**bold**
***bold italics***
_underline_
"""
        xml = """
<fountain>
  <action><i>italics</i>
<b>bold</b>
<b><i>bold italics</i></b>
<u>underline</u></action>
</fountain>
"""
        assert_transform(ft, xml)

    def test_combination(self):
        # "the writer can mix and match and combine bold, italics and
        # underlining, as screenwriters often do"
        ft = "From what seems like only INCHES AWAY.  _Steel's face FILLS the *Leupold Mark 4* scope_."
        xml = """
<fountain>
  <action>From what seems like only INCHES AWAY.  <u>Steel's face FILLS the <i>Leupold Mark 4</i> scope</u>.</action>
</fountain>"""
        assert_transform(ft, xml)

    def test_escape(self):
        # Original example has a colon after "keypad." I remove it
        # here: leaving it in makes the one-line screenplay into title
        # page with a key:value pair
        ft = "Steel enters the code on the keypad **\*9765\***"
        xml = """
<fountain>
  <action>Steel enters the code on the keypad <b>*9765*</b></action>
</fountain>"""
        assert_transform(ft, xml)

    # Python Markdown interprets the emphasis rules differently, and I
    # see little value in fighting it. Markdown imlementations
    # disagree on interpreting this example:
    # https://johnmacfarlane.net/babelmark2/?text=He+dialed+*69+and+then+*23%2C+and+then+hung+up.
    # A Python-Markdown extension existst (betterem) that can make
    # this test pass, if this becomes a user issue:
    # https://github.com/Python-Markdown/markdown/issues/910
    @pytest.mark.xfail
    def test_spaces_around_emphasis(self):
        # "As with Markdown, the spaces around the emphasis characters
        # are meaningful. In this example, the asterisks would not
        # trigger italics between them, because both have a space to
        # the left:"
        ft = "He dialed *69 and then *23, and then hung up."
        xml = """
<fountain>
  <action>He dialed *69 and then *23, and then hung up.</action>
</fountain>
"""
        assert_transform(ft, xml)

    def test_emphasis_actoss_words(self):
        # "But in this case, the text between the asterisks would be
        # italicized:"
        ft = "He dialed *69 and then 23*, and then hung up."
        xml = """
<fountain>
  <action>He dialed <i>69 and then 23</i>, and then hung up.</action>
</fountain>
"""
        assert_transform(ft, xml)

    def test_emphasis_across_words_with_escape(self):
        # "The writer would need to escape one or both of the
        # asterisks to avoid the accidental italics:"
        ft = "He dialed *69 and then 23\*, and then hung up."
        xml = """
<fountain>
  <action>He dialed *69 and then 23*, and then hung up.</action>
</fountain>
"""
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
<fountain>
  <action>As he rattles off the long list, Brick and Steel *share a look.

This is going to be BAD.*</action>
</fountain>
"""
        assert_transform(ft, xml)


class TestTitlePage:
    def test_tp(self):
        # "The optional Title Page is always the first thing in a
        # Fountain document. Information is encoding in the format
        # key: value. Keys can have spaces (e. g. Draft date), but
        # must end with a colon."
        #
        # "Values can be inline with the key or they can be indented
        # on a newline below the key (as shown with Contact
        # above). Indenting is 3 or more spaces, or a tab. The
        # indenting pattern allows multiple values for the same key
        # (multiple authors, multiple address lines)."
        ft = """
Title:
    _**BRICK & STEEL**_
    _**FULL RETIRED**_
Credit: Written by
Author: Stu Maschwitz
Source: Story by KTM
Draft date: 1/20/2012
Contact:
    Next Level Productions
    1588 Mission Dr.
    Solvang, CA 93463
"""
        xml = """
<fountain>
  <title-page>
    <key name="Title">
      <value><u><b>BRICK &amp; STEEL</b></u></value>
      <value><u><b>FULL RETIRED</b></u></value>
    </key>
    <key name="Credit">
      <value>Written by</value>
    </key>
    <key name="Author">
      <value>Stu Maschwitz</value>
    </key>
    <key name="Source">
      <value>Story by KTM</value>
    </key>
    <key name="Draft date">
      <value>1/20/2012</value>
    </key>
    <key name="Contact">
      <value>Next Level Productions</value>
      <value>1588 Mission Dr.</value>
      <value>Solvang, CA 93463</value>
    </key>
  </title-page>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)
    def test_min_tp(self):
        # "All Title Page parts are optional. So:
        ft = "Draft date: 6/23/2012"
        # ...on its own is a valid Title Page."
        xml = """
<fountain>
  <title-page>
    <key name="Draft date">
      <value>6/23/2012</value>
    </key>
  </title-page>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)

class TestPageBreaks:
    def test_page_breaks(self):
        # "Page Breaks are indicated by a line containing three or
        # more consecutive equals signs, and nothing more."
        ft = """
The General Lee flies through the air. FREEZE FRAME.

NARRATOR
Shoot, to the Dukes that's about like taking Grandma for a Sunday drive.

>**End of Act One**<

===

>**Act Two**<

The General Lee hangs in the air, right where we left it.  The NARRATOR'S voice kicks in.
"""
        xml = """
<fountain>
  <action>The General Lee flies through the air. FREEZE FRAME.</action>
  <dialogue>
    <character><name>NARRATOR</name></character>
    <line>Shoot, to the Dukes that's about like taking Grandma for a Sunday drive.</line>
  </dialogue>
  <action><center><b>End of Act One</b></center></action>
  <page-break></page-break>
  <action><center><b>Act Two</b></center>

The General Lee hangs in the air, right where we left it.  The NARRATOR'S voice kicks in.</action>
</fountain>
"""
        assert_transform(ft, xml)


class TestPunctuation:
    # There are no code examples in this secion of the spec
    pass

class TestLineBreaks:
    # "Unlike some markup languages, Fountain takes every carriage
    # return as intent."
    def test_classic_example(self):
        # "his allows the writer to control the spacing between
        # paragraphs in Action elements, as seen in this classic
        # example:"
        ft = """
Murtaugh, springing hell bent for leather -- and folks, grab your hats ... because just then, a BELL COBRA HELICOPTER crests the edge of the bluff.

An explosion of sound...
As it rises like an avenging angel ...
Hovers, shattering the air with turbo-throb, sandblasting the hillside with a roto-wash of loose dirt, tables, chairs, everything that's not nailed down ...

Screaming, chaos, frenzy.
Three words that apply to this scene.
"""
        xml = """
<fountain>
  <action>Murtaugh, springing hell bent for leather -- and folks, grab your hats ... because just then, a BELL COBRA HELICOPTER crests the edge of the bluff.

An explosion of sound...
As it rises like an avenging angel ...
Hovers, shattering the air with turbo-throb, sandblasting the hillside with a roto-wash of loose dirt, tables, chairs, everything that's not nailed down ...

Screaming, chaos, frenzy.
Three words that apply to this scene.</action>
</fountain>
"""
        assert_transform(ft, xml)
        # but semantic linebreaks fold adjacent lines
        xml = """
<fountain>
  <action>Murtaugh, springing hell bent for leather -- and folks, grab your hats ... because just then, a BELL COBRA HELICOPTER crests the edge of the bluff.

An explosion of sound... As it rises like an avenging angel ... Hovers, shattering the air with turbo-throb, sandblasting the hillside with a roto-wash of loose dirt, tables, chairs, everything that's not nailed down ...

Screaming, chaos, frenzy. Three words that apply to this scene.</action>
</fountain>
"""
        assert_transform(ft, xml, SEMANTIC_LINES)
    def test_force_action(self):
        # "There are some unusual cases where this will fail. If you
        # wrote something like this:
        ft = """
INT. CASINO - NIGHT

THE DEALER eyes the new player warily.

SCANNING THE AISLES...
Where is that pit boss?

No luck. He has no choice to deal the cards.
"""
        # "...Fountain would interpret SCANNING THE AISLES... as a
        # Character name"
        xml = """
<fountain>
  <scene>
    <scene-heading><setting>INT.</setting><location>CASINO</location><tod>NIGHT</tod></scene-heading>
    <action>THE DEALER eyes the new player warily.</action>
    <dialogue>
      <character><name>SCANNING THE AISLES...</name></character>
      <line>Where is that pit boss?</line>
    </dialogue>
    <action>No luck. He has no choice to deal the cards.</action>
  </scene>
</fountain>
"""
        assert_transform(ft, xml)
        # "To correct this, use a preceding ! to force the uppercase
        # line to be Action"
        ft = """
INT. CASINO - NIGHT

THE DEALER eyes the new player warily.

!SCANNING THE AISLES...
Where is that pit boss?

No luck. He has no choice to deal the cards.
"""
        xml = """
<fountain>
  <scene>
    <scene-heading><setting>INT.</setting><location>CASINO</location><tod>NIGHT</tod></scene-heading>
    <action>THE DEALER eyes the new player warily.

SCANNING THE AISLES...
Where is that pit boss?

No luck. He has no choice to deal the cards.</action>
  </scene>
</fountain>
"""
        assert_transform(ft, xml)
    def test_dialogue(self):
        # "Fountain will know that DEALER's dialogue should be one
        # continuous formatted block with forced line breaks."
        ft = """
DEALER
Ten.
Four.
Dealer gets a seven.  Hit or stand sir?

MONKEY
Dude, I'm a monkey.
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>DEALER</name></character>
    <line>Ten.
Four.
Dealer gets a seven.  Hit or stand sir?</line>
  </dialogue>
  <dialogue>
    <character><name>MONKEY</name></character>
    <line>Dude, I'm a monkey.</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)
        # "However, if you want to do the unconventional thing of
        # leaving white space in dialogue
        ft = """
DEALER
Ten.
Four.
Dealer gets a seven.

Hit or stand sir?

MONKEY
Dude, I'm a monkey.
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>DEALER</name></character>
    <line>Ten.
Four.
Dealer gets a seven.</line>
  </dialogue>
  <action>Hit or stand sir?</action>
  <dialogue>
    <character><name>MONKEY</name></character>
    <line>Dude, I'm a monkey.</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)
        # "You would need to type two spaces on your "blank" line so
        # that Fountain knows that Hit or stand sir? is not an Action
        # element:"
        ft = """
DEALER
Ten.
Four.
Dealer gets a seven.
  
Hit or stand sir?

MONKEY
Dude, I'm a monkey.
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>DEALER</name></character>
    <line>Ten.
Four.
Dealer gets a seven.

Hit or stand sir?</line>
  </dialogue>
  <dialogue>
    <character><name>MONKEY</name></character>
    <line>Dude, I'm a monkey.</line>
  </dialogue>
  <action/>
</fountain>
"""
        assert_transform(ft, xml)

class TestIndenting:
    def test_indents(self):
        # "Leading tabs or spaces in elements other than Action will
        # be ignored. If you choose to use them though, your Fountain
        # text file could look quite a bit more like a screenplay."
        ft = """
                CUT TO:

INT. GARAGE - DAY

BRICK and STEEL get into Mom's PORSCHE, Steel at the wheel.  They pause for a beat, the gravity of the situation catching up with them.

            BRICK
    This is everybody we've ever put away.

            STEEL
        (starting the engine)
    So much for retirement!

They speed off.  To destiny!
"""
        xml = """
<fountain>
  <transition>CUT TO:</transition>
  <scene>
    <scene-heading><setting>INT.</setting><location>GARAGE</location><tod>DAY</tod></scene-heading>
    <action>BRICK and STEEL get into Mom's PORSCHE, Steel at the wheel.  They pause for a beat, the gravity of the situation catching up with them.</action>
    <dialogue>
      <character><name>BRICK</name></character>
      <line>This is everybody we've ever put away.</line>
    </dialogue>
    <dialogue>
      <character><name>STEEL</name></character>
      <parenthetical>(starting the engine)</parenthetical>
      <line>So much for retirement!</line>
    </dialogue>
    <action>They speed off.  To destiny!</action>
  </scene>
</fountain>
"""
        assert_transform(ft, xml)

class TestNotes:
    def test_note(self):
        # "A Note is created by enclosing some text with double
        # brackets. Notes can be inserted between lines, or in the
        # middle of a line."
        ft = """
INT. TRAILER HOME - DAY

This is the home of THE BOY BAND, AKA DAN and JACK[[Or did we think of actual names for these guys?]].  They too are drinking beer, and counting the take from their last smash-and-grab.  Money, drugs, and ridiculous props are strewn about the table.

[[It was supposed to be Vietnamese, right?]]

JACK
(in Vietnamese, subtitled)
*Did you know Brick and Steel are retired?*"""
        # Not sure if Fountain would have the NOTE as part of the
        # action or outside it.
        xml = """
<fountain>
  <scene>
    <scene-heading><setting>INT.</setting><location>TRAILER HOME</location><tod>DAY</tod></scene-heading>
    <action>This is the home of THE BOY BAND, AKA DAN and JACK<note>Or did we think of actual names for these guys?</note>.  They too are drinking beer, and counting the take from their last smash-and-grab.  Money, drugs, and ridiculous props are strewn about the table.

<note>It was supposed to be Vietnamese, right?</note></action>
    <dialogue>
      <character><name>JACK</name></character>
      <parenthetical>(in Vietnamese, subtitled)</parenthetical>
      <line><i>Did you know Brick and Steel are retired?</i></line>
    </dialogue>
  </scene>
</fountain>
"""
        assert_transform(ft, xml)
    def test_multiline_note(self):
        # "Notes can contain carriage returns, but if you wish a note
        # to contain an empty line, you must place two spaces there to
        # "connect" the element into one."
        ft = """
His hand is an inch from the receiver when the phone RINGS.  Scott pauses for a moment, suspicious for some reason.[[This section needs work.
Either that, or I need coffee.
  
Definitely coffee.]] He looks around.  Phone ringing.
"""
        xml = """
<fountain>
  <action>His hand is an inch from the receiver when the phone RINGS.  Scott pauses for a moment, suspicious for some reason.<note>This section needs work.
Either that, or I need coffee.
  
Definitely coffee.</note> He looks around.  Phone ringing.</action>
</fountain>
"""
        assert_transform(ft, xml)
        # Without the two spaces, I'm not sure what the spec wants me
        # to do. As it stands, I keep looking for the closing ]]
        ft = """
His hand is an inch from the receiver when the phone RINGS.  Scott pauses for a moment, suspicious for some reason.[[This section needs work.
Either that, or I need coffee.

Definitely coffee.]] He looks around.  Phone ringing.
"""
        xml = """
<fountain>
  <action>His hand is an inch from the receiver when the phone RINGS.  Scott pauses for a moment, suspicious for some reason.<note>This section needs work.
Either that, or I need coffee.

Definitely coffee.</note> He looks around.  Phone ringing.</action>
</fountain>
"""
        assert_transform(ft, xml)

class TestBoneYard:
    def test_boneyard(self):
        # "If you want Fountain to ignore some text, wrap it with /*
        # some text */. In this example, an entire scene is put in the
        # boneyard. It will be ignored completely on formatted
        # output."
        ft = """
COGNITO
Everyone's coming after you mate!  Scorpio, The Boy Band, Sparrow, Point Blank Sniper...

As he rattles off the long list, Brick and Steel share a look.  This is going to be BAD.

CUT TO:
/*
INT. GARAGE - DAY

BRICK and STEEL get into Mom's PORSCHE, Steel at the wheel.  They pause for a beat, the gravity of the situation catching up with them.

BRICK
This is everybody we've ever put away.

STEEL
(starting the engine)
So much for retirement!

They speed off.  To destiny!

CUT TO:
*/
EXT. PALATIAL MANSION - DAY

An EXTREMELY HANDSOME MAN drinks a beer.  Shirtless, unfortunately.
"""
        xml = """
<fountain>
  <dialogue>
    <character><name>COGNITO</name></character>
    <line>Everyone's coming after you mate!  Scorpio, The Boy Band, Sparrow, Point Blank Sniper...</line>
  </dialogue>
  <action>As he rattles off the long list, Brick and Steel share a look.  This is going to be BAD.</action>
  <transition>CUT TO:</transition>
  <scene>
    <scene-heading><setting>EXT.</setting><location>PALATIAL MANSION</location><tod>DAY</tod></scene-heading>
    <action>An EXTREMELY HANDSOME MAN drinks a beer.  Shirtless, unfortunately.</action>
  </scene>
</fountain>
"""
        assert_transform(ft, xml)

class TestSectionsAndSynopses:
    def test_basics(self):
        # "Create a Section by preceding a line with one or more
        # pound-sign # characters"
        ft = """
CUT TO:

# This is a Section

INT. PALACE HALLWAY - NIGHT
"""
        xml = """
<fountain>
  <transition>CUT TO:</transition>
  <section heading="This is a Section">
    <scene>
      <scene-heading><setting>INT.</setting><location>PALACE HALLWAY</location><tod>NIGHT</tod></scene-heading>
      <action/>
    </scene>
  </section>
</fountain>
"""
        assert_transform(ft, xml)
    def test_multilevel(self):
        # "You can nest Sections by adding more # characters."
        ft = """
# Act

## Sequence

### Scene

## Another Sequence

# Another Act
"""
        xml = """
<fountain>
  <section heading="Act">
    <section heading="Sequence">
      <section heading="Scene"/>
    </section>
    <section heading="Another Sequence"/>
  </section>
  <section heading="Another Act">
    <action/>
  </section>
</fountain>
"""
        assert_transform(ft, xml)
    def test_synopses(self):
        # "Synopses are single lines prefixed by an equals sign
        # =. They can be located anywhere within the screenplay."
        ft = """
# ACT I

= Set up the characters and the story.

EXT. BRICK'S PATIO - DAY

= This scene sets up Brick & Steel's new life as retirees. Warm sun, cold beer, and absolutely nothing to do.

A gorgeous day.  The sun is shining.  But BRICK BRADDOCK, retired police detective, is sitting quietly, contemplating -- something.
"""
        xml = """
<fountain>
  <section heading="ACT I">
    <synopsis>Set up the characters and the story.</synopsis>
    <scene>
      <scene-heading><setting>EXT.</setting><location>BRICK'S PATIO</location><tod>DAY</tod></scene-heading>
      <synopsis>This scene sets up Brick &amp; Steel's new life as retirees. Warm sun, cold beer, and absolutely nothing to do.</synopsis>
      <action>A gorgeous day.  The sun is shining.  But BRICK BRADDOCK, retired police detective, is sitting quietly, contemplating -- something.</action>
    </scene>
  </section>
</fountain>
"""
        assert_transform(ft, xml)

DIR = os.path.dirname(os.path.abspath(__file__))
@pytest.mark.parametrize("f", glob.glob(os.path.join(DIR, "tests/*.ftx")))
def test_file_sample(f):
    basename = os.path.splitext(f)[0]
    arg_list = []
    try:
        basename, a = basename.split("~")
        arg_list.append(a)
    except ValueError:
        pass
    ft_filename = basename+".fountain"
    arg_list.append(ft_filename)
    args = fountainhead.arg_parser().parse_args(arg_list)
    xml = open(f).read()
    assert fountainhead.pprint(fountainhead.parse_fountain(args.infile, args)).strip() == xml.strip()
