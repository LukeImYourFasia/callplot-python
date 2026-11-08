<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output xmlns:xalan="http://xml.apache.org/xslt" encoding="UTF-8" method="xml"/>

  <xsl:template match="/">
<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:w="urn:schemas-microsoft-com:office:word"
xmlns="http://www.w3.org/TR/REC-html40">

<head>
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252"/>
<meta name="ProgId" content="Word.Document"/>
<meta name="Generator" content="Microsoft Word 9"/>
<meta name="Originator" content="Microsoft Word 9"/>
<style>
<!--
 /* Style Definitions */
p.MsoNormal, li.MsoNormal, div.MsoNormal
	{mso-style-parent:"";
	margin:0in;
	margin-bottom:.0001pt;
	mso-pagination:widow-orphan;
	font-size:12.0pt;
	font-family:"Times New Roman";
	mso-fareast-font-family:"Times New Roman";}
@page Section1
	{size:8.5in 11.0in;
	margin:1.0in 1.25in 1.0in 1.25in;
	mso-header-margin:.5in;
	mso-footer-margin:.5in;
	mso-paper-source:0;}
div.Section1
	{page:Section1;}
-->
</style>
</head>

<body lang='EN-US' style='tab-interval:.5in'>

<div class='Section1'>

		<pre><xsl:copy-of select="/plot/picture"/> </pre>

<table border='1' cellspacing='0' cellpadding='0' style='border-collapse:collapse;border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>

 <tr>

  <td width='64' valign='top' style='width:48.3pt;border:solid windowtext .5pt;  padding:0in 5.4pt 0in 5.4pt'>
  <p class='MsoNormal'><b>Number<o:p></o:p></b></p>
  </td>

  <td width='228' valign='top' style='width:171.0pt;border:solid windowtext .5pt;border-left:none;mso-border-left-alt:solid windowtext .5pt;padding:0in 5.4pt 0in 5.4pt'>
  <p class='MsoNormal'><b>Annotation<o:p></o:p></b></p>
  </td>

  <td width='307' valign='top' style='width:3.2in;border:solid windowtext .5pt;border-left:none;mso-border-left-alt:solid windowtext .5pt;padding:0in 5.4pt 0in 5.4pt'>
  <p class='MsoNormal'><b>Packet<o:p></o:p></b></p>
  </td>

 </tr>

<xsl:for-each select="/plot/message">

<tr> 

<td width='64' valign='top' style='width:48.3pt;border:solid windowtext .5pt;border-top:none;mso-border-top-alt:solid windowtext .5pt;padding:0in 5.4pt 0in 5.4pt'>
<p class='MsoNormal'>
<xsl:copy> 
<a name="t{number}"/>
<a href="#m{number}">
<xsl:value-of select="number"/> 
</a>
</xsl:copy>
</p>
</td>

<td width='228' valign='top' style='width:171.0pt;border-top:none;border-left:none;border-bottom:solid windowtext .5pt;border-right:solid windowtext .5pt;mso-border-top-alt:solid windowtext .5pt;mso-border-left-alt:solid windowtext .5pt;padding:0in 5.4pt 0in 5.4pt'>
<p class='MsoNormal'>
<xsl:for-each select="captions/caption">
<xsl:value-of select="text()"/> 
<br/>
</xsl:for-each>
<xsl:for-each select="notes/note">
<xsl:value-of select="text()"/> 
<br/>
</xsl:for-each>
</p>
</td>

<td width='307' valign='top' style='width:3.2in;border-top:none;border-left:none;border-bottom:solid windowtext .5pt;border-right:solid windowtext .5pt;mso-border-top-alt:solid windowtext .5pt;mso-border-left-alt:solid windowtext .5pt;padding:0in 5.4pt 0in 5.4pt'>
<p class='MsoNormal'><span style='font-family:"Courier New"'>
<xsl:for-each select="comments/comment">
<xsl:value-of select="text()"/> 
<br/>
</xsl:for-each>
<o:p></o:p></span></p>
</td>

</tr>
</xsl:for-each>

</table>

</div>

</body>

</html>

</xsl:template>

</xsl:stylesheet>
