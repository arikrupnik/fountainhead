<!-- Extract plot summary from a Fountain screenplay with synopsys elements -->

<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  
  <xsl:output method="text"/>

  <xsl:template match="title-page | text()">
    <!-- omit metadata and character content by default but descend into elements -->
  </xsl:template>

  <xsl:template match="synopsis//text()">
    <xsl:value-of select="."/>
    <xsl:choose>
      <xsl:when test="../following-sibling::synopsis">
        <xsl:text>&#xa;</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text> </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
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
