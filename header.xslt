<!-- Extract header information from a Fountain screenplay -->

<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  
  <xsl:output method="text"/>

  <xsl:template match="/fountain">
    <xsl:for-each select="title-page">
      <xsl:for-each select="key[@name='Title']">
        <xsl:text># </xsl:text>
        <xsl:value-of select="value"/>
        <xsl:text>&#xa;&#xa;</xsl:text>
      </xsl:for-each>
      <xsl:for-each select="key[@name='Logline']">
        <xsl:value-of select="value"/>
        <xsl:text>&#xa;&#xa;</xsl:text>
      </xsl:for-each>
      <xsl:for-each select="key[@name='Project Home']">
        <xsl:text>## &lt;</xsl:text>
        <xsl:value-of select="value"/>
        <xsl:text>&gt;&#xa;&#xa;</xsl:text>
      </xsl:for-each>
      <xsl:for-each select="key[@name='Version']">
        <xsl:text>### revision: </xsl:text>
        <xsl:value-of select="value"/>
        <xsl:text>&#xa;&#xa;</xsl:text>
      </xsl:for-each>
    </xsl:for-each>
    <xsl:text>&#xa;&#xa;</xsl:text>
  </xsl:template>

</xsl:transform>
