<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output xmlns:xalan="http://xml.apache.org/xslt" encoding="UTF-8" method="xml"/>

  <xsl:template match="/">
    <html>
      <body>
	<pre><xsl:copy-of select="/plot/picture"/> </pre>

	<table border='true'>
	  <xsl:for-each select="/plot/message">

	    <tr> 
	<td>
		<xsl:copy> 
		  <a name="t{number}"/>
		  <a href="#m{number}">
		  <xsl:value-of select="number"/> 
		  </a>
		</xsl:copy>
	      </td> 
	      
	      <td>
		  <xsl:for-each select="notes/note">
		    <xsl:value-of select="text()"/> 
		    <br/>
		  </xsl:for-each>
	      </td>
	      <td>
	<tt>
		  <xsl:for-each select="comments/comment">
		    <xsl:value-of select="text()"/> 
		    <br/>
		  </xsl:for-each>
	</tt>
	      </td>
	    </tr>
	  </xsl:for-each>
	</table>
      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>
