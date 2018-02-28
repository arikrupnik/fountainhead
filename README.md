# fountainhead
Tools for using Fountain.io screenplays throughout production process

## fountainhead.py: converts .fountain files to XML
Fully implements the [Fountatin spec](https://fountain.io/syntax).
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

