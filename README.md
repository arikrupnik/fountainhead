# Fountainhead
Tools for using Fountain.io screenplays throughout production process

## `fountainhead.py`: converts .fountain files to XML
Fully implements the [Fountain spec](https://fountain.io/syntax).
Requires [Python Markdown](https://pypi.python.org/pypi/Markdown) (`$ pip install markdown`).
Outputs semantic XML that corresponds to implicit structure in .fountain documents.

Input:

    INT. HOUSE - DAY
    
    MARY (O.S.)
    I can't believe how easy it is to write in Fountain.
    
    TOM
    (typing)
    Look! I just made a parenthetical!


Output:

    <?xml version="1.0"?>
    <?xml-stylesheet href="ftx.css"?>
    <fountain>
      <scene>
        <scene-heading>INT. HOUSE - DAY</scene-heading>
        <dialogue>
          <character>
            <name>MARY</name>
            <extension>(O.S.)</extension>
          </character>
          <line>I can't believe how easy it is to write in Fountain.</line>
        </dialogue>
        <dialogue>
          <character>
            <name>TOM</name>
          </character>
          <parenthetical>(typing)</parenthetical>
          <line>Look! I just made a parenthetical!</line>
        </dialogue>
      </scene>
    </fountain>

The output can display directly in browsers with the use of included CSS stylesheet, or further convert to PDF using [Weasyprint](http://weasyprint.org) and the included makefile.

## Syntax extensions

### Section identifiers

Fountainhead parses identifiers out of section headings in addition to scene headings.
`#ACT II #ii#` becomes `<section heading="Act II" id="ii">`

At user option (`-x` or `--syntax-extensions` switch), Fountainhead interprets additional syntax outside the scope of the Fountain spec.

### `=<include.fountain`
Fountainhead parses the file named `include.fountain` and inserts its parse tree in place of this directive.
This feature allows breaking a screenplay into smaller files that are easier to edit individually.
Changing the order of scenes, for example, means moving one line instead of hundreds at a time.

Fountainhead parses the include first, rather than including its source directly. This keeps includes from messing up the structure of the including file. Any scene or section that starts in a file ends in the same file.

If the filename includes a fragment identifier (e.g., `file.fountain#scene_id`), Fountainhead includes only the scene or section with that identifier.
A common use case for this feature is keeping "mirror" scenes together for editing.
For example, two characters may have a confrontation at the beginning of a screenplay and the end; the differences between these interactions show character development.
It's easy to keep the mirror images consistent if they reside in the same file.

### Semantic linebreaks

By default, Fountainhead follows the [Fountain spec](https://fountain.io/syntax#section-br): "Unlike some markup languages, Fountain takes every carriage return as intent." At user option (`-s` or `--semantic-linebreaks` switch), Fountainhead collapses single linefeeds into spaces. <http://rhodesmill.org/brandon/2012/one-sentence-per-line>

## `plot-summary.xslt`: extracts plot summary from a Fountain screenplay

I like to start a screenplay by writing a treatment or a plot summary.
I can use it to gauge interest in my story, and solicit early feedback.
Once I start writing action and dialog, it's convenient to have the plot summary and the screenplay in the same place.
It's easy to reference the summary as I'm developing the story, and it's easy to keep the summary up to date as the story evolves.
Keeping the summary in `=synopsis` elements inside a .fountain screenplay allows me to keep one source of truth.
This stylesheet extracts these synopses along with section headings and outputs them as plain markdown.
The output includes `Title` and `Logline` keys when those are present in the .fountain source.
