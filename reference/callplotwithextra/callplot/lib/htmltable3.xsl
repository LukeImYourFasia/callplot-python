<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output xmlns:xalan="http://xml.apache.org/xslt" encoding="UTF-8" method="xml"/>

  <xsl:template match="/">
    <html>
      <body>
	<small><small><pre><xsl:copy-of select="/plot/picture"/></pre></small></small>

	<table border='1'>
		<tr>
	<th>Seq</th>
	<th>Message and Details</th>
	<th>Notes</th>
		</tr>
		
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
		  <xsl:for-each select="captions/caption">
		    <strong><xsl:value-of select="text()"/></strong> 
		    <br/>
		  </xsl:for-each>
		  <xsl:for-each select="notes/note">
		    <code><xsl:value-of select="text()"/></code> 
		    <br/>
		  </xsl:for-each>
	      </td>
	      <td>
		  <xsl:for-each select="comments/comment">
		    <xsl:value-of select="text()"/> 
		    <br/>
		  </xsl:for-each>
	      </td>
	    </tr>
	  </xsl:for-each>
	</table>
      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>
