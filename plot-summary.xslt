<!-- Extract plot summary from a Fountain screenplay with synopsys elements -->

<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  
  <xsl:output method="text"/>

  <xsl:template match="/fountain">
    <xsl:for-each select="title-page/key[@name='Title']">
      <xsl:text># </xsl:text>
      <xsl:value-of select="value"/>
      <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="title-page/key[@name='Logline']">
      <xsl:value-of select="value"/>
      <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="title-page/key[@name='Project Home']">
      <xsl:text>## &lt;</xsl:text>
      <xsl:value-of select="value"/>
      <xsl:text>&gt;&#xa;&#xa;</xsl:text>
    </xsl:for-each>
    <xsl:text># Plot Summary</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>&#xa;&#xa;</xsl:text>
  </xsl:template>

  <xsl:template match="title-page | text()">
    <!-- omit metadata and character content by default but descend into elements -->
  </xsl:template>

  <xsl:template match="synopsis//text()">
    <xsl:value-of select="."/>
    <xsl:if test="../following-sibling::synopsis">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="section">
    <xsl:text>&#xa;&#xa;</xsl:text>
    <xsl:call-template name="indent">
      <xsl:with-param name="indent" select="'#'"/>
      <xsl:with-param name="count" select="count(ancestor-or-self::section)+1"/>
    </xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:value-of select="@heading"/>
    <xsl:text>&#xa;&#xa;</xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template name="indent">
    <xsl:param name="indent"/>
    <xsl:param name="count" select="0"/>
    <xsl:if test="$count > 0">
      <xsl:value-of select="$indent"/>
      <xsl:call-template name="indent">
        <xsl:with-param name="indent" select="$indent"/>
        <xsl:with-param name="count" select="$count - 1"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

</xsl:transform>
