# fountainhead
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

## `plot-summary.xslt`: extracts plot summary from a Fountain screenplay

I like to start a screenplay by writing a treatment or a plot summary.
I can use it to gauge interest in my story, and solicit early feedback.
Once I start writing action and dialog, it's convenient to have the plot summary and the screenplay in the same place.
It's easy to reference the summary as I'm developing the story, and it's easy to keep the summary up to date as the story evolves.
Keeping the summary in `=synopsis` elements inside a .fountain screenplay allows me to keep one source of truth.
This stylesheet extracts these synopses along with section headings and outputs them as plain markdown.
The output includes `Title` and `Logline` keys when those are present in the .fountain source.
