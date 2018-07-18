<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  
  <xsl:output method="html" indent="yes"/>
  
  <xsl:template match="/">
    <style>
      table {
        border-collapse: collapse;
      }
      table, th, td {
        border: 1px solid black;
      }
      td {
        padding: 0.3em;
      }
    </style>
    <table>
      <tr>
        <th>ord</th>
        <th>act</th>
        <th>scene</th>
        <th>location</th>
        <th>characters</th>
        <th>synopsis</th>
      </tr>
      <xsl:apply-templates select=".//scene"/>
    </table>
  </xsl:template>

  <xsl:template match="scene">
    <tr>
      <td>
        <xsl:value-of select="count(preceding::scene)+1"/>
      </td>
      <td>
        <xsl:value-of select="ancestor::section[last()]/@heading"/>
      </td>
      <td>
        <xsl:value-of select="@id"/>
      </td>
      <td>
        <xsl:value-of select="*/location"/>
      </td>
      <td>
        <xsl:for-each select="breakdown/character-ref">
          <xsl:value-of select="."/>
          <xsl:value-of select="' '"/>
        </xsl:for-each>
      </td>
      <td>
        <xsl:value-of select="synopsis"/>
      </td>
    </tr>
  </xsl:template>
  
</xsl:transform>
  
