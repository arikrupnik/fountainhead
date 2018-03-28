<!-- Minimalist CSS to render markdown in typewriter sytle consistent
     with common screenplay formatting. This file includes CSS rules
     as well as the <style> tag; the use case is passing it as an
     "--include-in-header" option to pandoc, which needs the HTML
     envelope. -->
<style type="text/css">
* { font-family: courier, monospace; font-size: 12pt; }
body { width: 7in; }
em { text-decoration: underline; font-style: inherit; }
ol, ul { padding-left: 1em; }
h1, h2, h3, h4, h5, h6 { text-align: center; font-weight: normal; }
h1 { text-transform: uppercase; font-weight: bold; }
h1, h2 { text-decoration: underline; }
*+h1 { margin-top: 18pt; }

@media print {
  @page {
            size: Letter;
            /*margin: 0in 0.44in 0.2in 0.44in;*/
            margin-top: .5in;
            margin-bottom: .5in;
            margin-left: .75in;
        }
  /*body { margin: 1in; }*/
  h1, h1, h2, h3, h4, h5, h6 { page-break-after: avoid }
}

</style>
