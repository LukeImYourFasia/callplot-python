/*
 * Copyright (C) 2004 dynamicsoft, Inc.
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License
 * as published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA
 * 
 * Contact information: 
 * 
 * David Ladd
 * dynamicsoft
 * 600 Lanidex Plaza
 * Parsippany, NJ 07054
 * 
 * http://www.dynamicsoft.com 
 * 
 */

package com.dynamicsoft.callplot;

import java.util.*;
import java.io.*;

public class Player implements CallplotConstants {
    private char[][] caption;
    private String captionString;
    private String name;
    private char[] glyph;
    private char[] blank;
    private int column;
    private Flow flow;
	
	
	private	static int id = 1000000;
	
    private static final String lineDelimiter = "^";

    public Player( Flow flow, String name, String caption ) {
	this.glyph = arrayOf( "|" );
	this.blank = arrayOf( " " );
	this.column = 10;
	this.name = name;
	digest( caption );
	this.flow = flow;
    }

    public void setColumn( int column ) {
	this.column = column;
    }

    public int getColumn() {
	return this.column;
    }

    public int getCaptionLines() {
	return this.caption.length;
    }

    public String getName() {
	return this.name;
    }

    private void digest( String captionString ) {
	String newCaptionString = "";
	StringTokenizer st = new StringTokenizer( captionString, lineDelimiter );
	int count = st.countTokens();
	this.caption = new char[count][];
	for ( int i = 0; i < count; i++ ) {
	    String thisLine = st.nextToken();
	    this.caption[i] = arrayOf( thisLine );
	    // pic wants multiple lines like this:
	    // "line 1" "line 2" "line 3"
	    if ( i != 0 ) {
		newCaptionString += "\" \"";
	    }
	    newCaptionString += thisLine;
	}
	this.captionString = newCaptionString;
    }

    private char[] arrayOf( String s ) {
	int len = s.length();
	char[] ret = new char[ len ];
	s.getChars( 0, len, ret, 0);
	return ret;
    }

    public void drawSelf( int line, char[] buffer ) {
	char[] image;
	int lineInCaption = flow.labelLine( line );
	if ( lineInCaption >= 0 ) {
	    if ( lineInCaption < caption.length ) {
		image = caption[lineInCaption];
	    } else {
		image = blank;
	    }

	} else {
	    image = glyph;
	}
	if ( image.length == 1 ) {
	    buffer[ this.column ] = image[0];
	} else {
	    int width = image.length;
	    int bias = width / 2;
	    System.arraycopy( image, 0, buffer, this.column - bias, width );
	}
    }

    static int mynum = 0;

    public void drawPictureOn( Flow f, PrintWriter out, int mode ) {
        if ( (mode & PIC) != 0 ) {
            out.print( "P" + name + ": { box \"" + this.captionString +
                       "\"; down; L" + name + ": line " + (f.getTotalHeight()/6.0 + 0.25D) + "i from last box.s }; right; move 2i\n" );
        } else if ( (mode & SVG) != 0 ) {
            // scale the width per the desired percentage
            double wid = f.getColumnPitch() * Integer.parseInt(f.getVMLBoxWidthPercentage()) / 100.0;
            double ht = 2.0D;
            double stagger = f.getStagger() ? ((ht + 2.0D) * (mynum++ % 2.0D)) : 0.0D;
            double ycenter = stagger  - ht / 2.0D;
            double center = (this.column * f.getVMLXSize()) / f.getTotalWidth(); 

            out.print("<rect x='" + 
                      (center - wid/2.0D) + "' y='" + (ycenter - ht/2.0D) + "' width='" + wid + 
                      "' height='" + ht + "' rx='.6' ry='.6' filter='url(#dropShadow)'>");
            out.print("</rect>\n");

            for( int i = 0; i < caption.length; i++ ) {
                out.println(" <text text-anchor='middle' y='" + (ycenter + i + 0.4) + "' x='" + center + "'>");
                out.println( f.xmlEscape(new String(caption[i])) );
                out.println(" </text> ");
            }

            out.print("<line x1='" + center + "' y1='" + (ycenter - ht/2.0D + ht) +
                      "' x2='" + center + "' y2='" + f.getVMLYSize() + "'>");
            out.print("</line>\n");
        } else if ( (mode & VML) != 0 ) {
            int wid = (f.getColumnPitch() * f.getVMLXSize()) / f.getTotalWidth();

            // scale the width per the desired percentage
            wid *= Integer.parseInt(f.getVMLBoxWidthPercentage());  
            wid /= 100;

            double ht = 4.0D;
            double stagger = f.getStagger() ? ((ht + 2.0D) * (mynum++ % 2.0D)) : 0.0D;
            double ycenter = stagger  - ht / 2.0D;
            double center = (this.column * f.getVMLXSize()) / f.getTotalWidth(); 

            out.print("<v:rect " + f.getVMLBoxStyle() + " style='position:absolute;left:" + 
                      (center - wid/2.0D) + ";top:" + (ycenter - ht/2.0D) + ";width:" + wid + 
                      ";height:" + ht + "'>");
            out.println("  <v:stroke   " + f.getVMLStyle() + " />");
            out.print("</v:rect>");

            out.println(" <v:shape fillcolor='black' strokeweight='0pt' coordorigin='0 0' coordsize='100 100' style='position:absolute;top:" +
                        (0.2D + ycenter) + ";left:" + (center-wid/2.0D + 0.3D) + ";width:" + wid + ";height:"+ ht + "' path = 'm 0,0 l 100,0  e'>");
            
            out.println(" <v:path textpathok='True'/> ");
            out.println(" <v:textpath on='True' string=\"" + 
                        f.xmlEscape(new String(caption[0])) + 
                        "\" " + f.getVMLBoxTextStyle() + "/> ");
            out.println(" </v:shape> ");

            out.print("<v:line  from='" + center + "," + (ycenter - ht/2.0D + ht) +"' to='" + center + "," + f.getVMLYSize() + "'>");
            out.println("  <v:stroke " + f.getVMLStyle() + " />");
            out.print("</v:line>");
        }
		else
		{
			if ( (mode & GRAFFLE) != 0 )
			{
				// scale the width per the desired percentage
				double wid = GRAFFLE_MULT * f.getColumnPitch() * Integer.parseInt(f.getVMLBoxWidthPercentage()) / 100.0;
				double ht = 1.6D * caption.length * GRAFFLE_MULT;
				double stagger = f.getStagger() ? ((ht + 2.0D) * (mynum++ % 2.0D)) : 0.0D;
				double ycenter = (stagger * GRAFFLE_MULT + GRAFFLE_TOP_MARG) / 2.0D;
				double center = (this.column * f.getVMLXSize() * GRAFFLE_MULT) / f.getTotalWidth();
				
				
				
				
				// text box
				out.println("<dict>");
				
				out.println ("<key>Bounds</key>");
				out.println ("<string>{{" + (center - wid/2.0D) + ", " + (ycenter - ht/2.0D) +
							 " }, {" + wid +
							 ", " + ht + "}}</string>");
				
				out.println("<key>Class</key>");
				out.println("<string>ShapedGraphic</string>");
				out.println("<key>FitText</key>");
				out.println("<string>NO</string>");
				out.println("<key>ID</key>");
                int textId = ++id;
				out.println("<integer>" + id + "</integer>");
				
				out.println("<key>Shape</key>");
				out.println("<string>Rectangle</string>");
                
                out.println("<key>Style</key>");
                out.println("<dict>");
                {
                    out.println("<key>shadow</key>");
                    out.println("<dict>");
                    {
                        
                        out.println("<key>Draws</key>");
                        out.println("<string>YES</string>");
                        out.println("</dict>");
                    }
                    
                    out.println ("<key>fill</key>");
                    out.println ("<dict>");
                    {
                        out.println ("<key>FillType</key>");
                        out.println ("<integer>3</integer>");
                        
                        out.println ("<key>GradientCenter</key>");
                        out.println ("<string>{0.266667, -0.190476}</string>");
                        
                        out.println ("<key>GradientColor</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>a</key>");
                            out.println ("<string>0.51</string>");
                            out.println ("<key>b</key>");
                            out.println ("<string>0.869565</string>");
                            out.println ("<key>g</key>");
                            out.println ("<string>0.869565</string>");
                            out.println ("<key>r</key>");
                            out.println ("<string>0.869565</string>");
                            out.println ("</dict>");
                        }
                        out.println ("</dict>");
                    }
                    
                    out.println ("<key>stroke</key>");
                    out.println ("<dict>");
                    {
                        out.println ("<key>CornerRadius</key>");
                        out.println ("<real>5</real>");
                        
                        out.println ("<key>Color</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>a</key>");
                            out.println ("<string>0.14</string>");
                            out.println ("<key>b</key>");
                            out.println ("<string>0</string>");
                            out.println ("<key>g</key>");
                            out.println ("<string>0</string>");
                            out.println ("<key>r</key>");
                            out.println ("<string>0</string>");
                            out.println ("</dict>");
                        }
                        out.println ("</dict>");
                    }
                    out.println ("</dict>");
                }
				
                
				out.println("<key>Text</key>");
				out.println("<dict>");
                {
                    out.println("<key>Align</key>");
                    out.println("<integer>0</integer>");
                    out.println("<key>Text</key>");
                    out.println("<string>{\\rtf1\\mac\\ansicpg10000\\cocoartf824\\cocoasubrtf110");
                    out.println("{\\fonttbl\\f0\\fswiss\\fcharset77 Helvetica;}");
                    out.println("{\\colortbl;\\red255\\green255\\blue255;}");
                    out.println("\\pard\\tx560\\tx1120\\tx1680\\tx2240\\tx2800\\tx3360\\tx3920\\tx4480\\tx5040\\tx5600\\tx6160\\tx6720\\qc");
                    out.print("\\f0\\fs24 \\cf0 ");
                    int i;
                    for ( i = 0; i < (caption.length - 1); i++ )
                    {
                        out.println(new String (caption[i]) + "\\");
                    }
                    out.println(new String (caption[i]) + "}</string>");
                    out.println("</dict>");
                }
                
				out.println("</dict>");
				
                
                // Line
				out.println ("<dict>");
				out.println ("<key>Class</key>");
				out.println ("<string>LineGraphic</string>");
                
				out.println ("<key>ID</key>");
				out.println ("<integer>" + ++id + "</integer>");
                
				out.println ("<key>Points</key>");
				out.println ("<array>");
                {
                    out.println ("<string>{" + center + ", " + (ycenter - ht/2.0D + ht) + "}</string>");
                    out.println ("<string>{" + center + ", " + (GRAFFLE_TOP_MARG + (f.getVMLYSize() * GRAFFLE_MULT)) + "}</string>");
                    out.println ("</array>");
                }
				
				out.println ("<key>Style</key>");
				out.println ("<dict>");
                {
                    out.println ("<key>stroke</key>");
                    out.println ("<dict>");
                    {
                        out.println ("<key>Cap</key>");
                        out.println ("<integer>0</integer>");
                        
                        out.println ("<key>HeadArrow</key>");
                        out.println ("<string>0</string>");
                        
                        out.println ("<key>HeadScale</key>");
                        out.println ("<real>0.5</real>");
                        
                        out.println ("<key>TailArrow</key>");
                        out.println ("<string>0</string>");
                        
                        out.println ("<key>TailScale</key>");
                        out.println ("<real>0.5</real>");
                        out.println ("</dict>");
                    }
                    
                    out.println ("</dict>");
                }
				
				// link to text box
				out.println ("<key>Tail</key>");
				out.println ("<dict>");
                {
                    out.println ("<key>ID</key>");
                    // id is of text box
                    out.println ("<integer>" + textId + "</integer>");
                    out.println ("</dict>");
                }
				
				out.println ("</dict>");
				

			}
		}
    }
}
