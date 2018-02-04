<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
               version="1.0">

  <!-- Reconstitutes hierarchical structure in TextPlay output XML -->

  <!-- Wraps scenes in `scene' elements. If scene heading includes
       scene identifier, adds `id' attribute. Assumptions:
       `sceneheading' elements intorduce new scenes; transitions occur
       between scenes only, so a CUT TO: forces a new scene. -->
  
  <xsl:output method="xml" indent="yes"/>

  <xsl:strip-space elements="*"/>

  <xsl:template match="*" mode="copy">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates mode="copy"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="text()" mode="copy">
    <!-- textplay replaces regular hyphens with Unicode non-breaking ones -->
    <xsl:value-of select="translate(., '&#8209;', '-')"/>
  </xsl:template>

  <xsl:template match="character[contains(., '(')]" mode="copy">
    <xsl:copy>
      <xsl:attribute name="extension">
        <xsl:value-of select="translate(substring-after(., '('), ')', '')"/>
      </xsl:attribute>
      <xsl:value-of select="normalize-space(substring-before(., '('))"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template name="copy-siblings-until-delimiter">
    <xsl:param name="next-delimiter"/>
    <xsl:choose>
      <xsl:when test="$next-delimiter">
        <xsl:apply-templates
            mode="copy"
            select="following-sibling::*[following-sibling::*[generate-id(.)=generate-id($next-delimiter)]]"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates
            mode="copy"
            select="following-sibling::*"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/*">
    <xsl:variable name="first-delimiter" select="(sceneheading|transition)[1]"/>
    <xsl:processing-instruction name="xml-stylesheet">
      <xsl:text>type="text/css" href="fountainhead/ftx.css"</xsl:text>
    </xsl:processing-instruction>
    <xsl:text>&#10;</xsl:text>
    <fountain>
      <front-matter>
        <xsl:copy-of select="*[following-sibling::*[generate-id(.)=generate-id($first-delimiter)]]"/>
      </front-matter>
      <xsl:for-each select="sceneheading|transition">
        <xsl:variable name="next-delimiter"
                      select="(following-sibling::sceneheading|following-sibling::transition)[1]"/>
        <xsl:choose>
          <xsl:when test="self::sceneheading">
            <xsl:variable name="id" select="substring-after(., '#')"/>
            <scene>
              <xsl:if test="$id">
                <xsl:attribute name="id">
                  <xsl:value-of select="translate($id, '#', '')"/>
                </xsl:attribute>
              </xsl:if>
              <xsl:copy>
                <xsl:choose>
                  <xsl:when test="$id">
                    <xsl:value-of select="normalize-space(substring-before(., '#'))"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="."/>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:copy>
              <xsl:call-template name="copy-siblings-until-delimiter">
                <xsl:with-param name="next-delimiter" select="$next-delimiter"/>
              </xsl:call-template>
            </scene>
          </xsl:when>
          <xsl:otherwise>
            <xsl:copy-of select="."/>
            <xsl:call-template name="copy-siblings-until-delimiter">
              <xsl:with-param name="next-delimiter" select="$next-delimiter"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </fountain>
  </xsl:template>

  <xsl:template match="slug" mode="copy">
    <action>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates mode="copy"/>
    </action>
  </xsl:template>
  
</xsl:transform>
