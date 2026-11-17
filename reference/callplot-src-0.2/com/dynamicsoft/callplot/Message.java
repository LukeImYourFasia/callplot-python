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

public class Message implements CallplotConstants {
    private static final String lineDelimiter = "^";
    private char filler = '-';
    private boolean arrowFrom = false;
    private boolean arrowTo = true;
    
    private String from;
    private String to;
    
    private int line;
    
    private char[][] caption;
    private String captionString;
    
    private boolean repeatLabel = false;
    
    private Vector notes;
    
    private Vector comments;
    
    private Flow flow;
    
    private int myNumber;
	
	private	static int id = 1;
	
    private char[] arrayOf( String s ) {
		int len = s.length();
		char[] ret = new char[ len ];
		s.getChars( 0, len, ret, 0);
		return ret;
    }
    
    public void setLine( int line ) {
		this.line = line;
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
    
    public Message( Flow flow, String from, String to, String caption ) {
		this( flow, from, to, caption, '-', false, true , "" );
    }    
    
    
    public Message( Flow flow, String from, String to, String caption, 
                   char lineChar, boolean arrowFrom, boolean arrowTo,
                   String comment )
    {
        this( flow, from, to, caption, lineChar, arrowFrom, arrowTo,
             comment, false );
    }
    
    public Message( Flow flow, String from, String to, String caption, 
                   char lineChar, boolean arrowFrom, boolean arrowTo,
                   String comment, boolean repeatLabel ) {
		this.flow = flow;
		this.from = from;
		this.to = to;
		digest( caption );
		this.filler = lineChar;
		this.arrowFrom = arrowFrom;
		this.arrowTo = arrowTo;
		this.comments = new Vector();
		this.notes = new Vector();
		if ( comment != null ) {
            this.comments.addElement( comment );
        }
        this.repeatLabel = repeatLabel;
    }
    
    public int getLength ()
    {
        return caption.length;
    }
    
    public void drawSelf( int line, char[] lineBuffer ) {
		int fcol = flow.columnOf( from );
		int tcol = flow.columnOf( to );
        
		int locol = fcol < tcol ? fcol : tcol;
		int hicol = fcol < tcol ? tcol : fcol;
        
		int offset = this.line - line; 
        
		if ( offset == 0 && locol != hicol ) {
			// this is our line -- draw the arrow
			for ( int j = locol + 1; j < hicol; j++ ) {
				lineBuffer[j] = filler;
			}
            
			if ( this.arrowFrom && locol == fcol || this.arrowTo && locol == tcol ) {
				lineBuffer[locol + 1] = '<';
			}
            
			if ( this.arrowFrom && hicol == fcol || this.arrowTo && hicol == tcol ) {
				lineBuffer[hicol - 1] = '>';
			}
            
		} else if ( offset == this.caption.length && (locol != hicol || flow.getDoNoteNumbering()) ) {
			// this the right line for our first caption line
			int num = -1;
			num = flow.nextMessageNumber();
            
            char[] finalCaption = null;
			if ( num != -1 ) {
				this.myNumber = num;
                finalCaption = arrayOf( "(" + num + ") " + new String( caption[0] ) );
			} else {
                finalCaption = caption[0];
            }
            
			int copySize = finalCaption.length;
			if ( locol + 1 + finalCaption.length > lineBuffer.length ) {
				copySize = lineBuffer.length - (locol + 1);
			}
			System.arraycopy( finalCaption, 0, lineBuffer, locol + 1, copySize );
			if ( copySize != finalCaption.length ) {
				lineBuffer[ lineBuffer.length - 1 ] = '*';
			}
		} else if ( offset > 0 && offset <= this.caption.length ) {
			// this is a non-initial caption line
			int idx = this.caption.length - offset;
			int copySize = caption[idx].length;
			if ( locol + 1 + caption[idx].length > lineBuffer.length ) {
				copySize = lineBuffer.length - (locol + 1);
			}
			System.arraycopy( caption[idx], 0, lineBuffer, locol + 1, copySize );
			if ( copySize != caption[idx].length ) {
				lineBuffer[ lineBuffer.length - 1 ] = '*';
			}
		}
    }
    
    public void addComment( String comment ) {
        this.comments.addElement( comment );
    }
    
    public void addNote( String note ) {
        this.notes.addElement( note );
    }
    
    public void printComment( PrintWriter out ) {
		if ( myNumber != 0 ) {
			out.println( "<message>" );
            
			out.println( "<number>" + myNumber + "</number>" );
            
			out.println( "<captions>" );
			for ( int i = 0; i < this.caption.length; i++ ) {
				out.println( "<caption>" + new String( this.caption[i] ) + "</caption>" );		
			}
			out.println( "</captions>" );
            
			out.println( "<notes>" );
            for ( int i = 0; i < this.notes.size(); i++ ) {
                String c = (String)this.notes.elementAt( i );
                out.println( "<note>" );
                out.println( c );
                out.println( "</note>" );
            }
			out.println( "</notes>" );
            
			out.println( "<comments>" );
            for ( int i = 0; i < this.comments.size(); i++ ) {
                String c = (String)this.comments.elementAt( i );
                out.println( "<comment>" );
                out.println( c );
                out.println( "</comment>" );
            }
			out.println( "</comments>" );
            
			out.println( "</message>" );
		}
    }
    
    private void textout( PrintWriter out, double textx, double texty, int line, String text ) {
        out.println(" <text y='" +
                    (texty + line) + "' x='" + textx + "'>");
        out.println( text );
        out.println(" </text> ");
    }
    
    public void drawPictureOn( Flow f, PrintWriter out, int mode )
    {
        if ( (mode & PIC) != 0 )
        {
            double off = -1.0D * line / 6.0D;
            if ( from.equals( to ) )
            {
                out.print( "{ line invis \"" + this.captionString + "\" \"\" from L" + 
                          from + ".start + (0," + off + ") to L" + 
                          to + ".start + (0.1," + off + ");  }\n" );
            } else if ( !this.arrowFrom && !this.arrowTo ) {
                out.print( "{ line dotted \"" + this.captionString + "\" \"\" from L" + 
                          from + ".start + (0," + off + ") to L" + 
                          to + ".start + (0," + off + ");  }\n" );
            } else {
                out.print( "{ arrow \"" + this.captionString + "\" \"\" from L" + 
                          from + ".start + (0," + off + ") to L" + 
                          to + ".start + (0," + off + ");  }\n" );
            }
        }  //PIC
        else if ( (mode & SVG) != 0 )
        {
            int fx = flow.columnOf( from );
            int tx = flow.columnOf( to );
            int startx = fx < tx ? fx : tx;
            double textx = 0.2 + startx;
            double texty = -0.2 + line;
            double arrowx = 0.4;
            
            if ( from.equals( to ) ) {
                for ( int i = 0; i < caption.length; i++ ) {
                    textout( out, textx, texty, i, f.xmlEscape( new String(caption[i]) ) );
                }
            } else if ( !this.arrowFrom && !this.arrowTo ) {
                for ( int i = 0; i < caption.length; i++ ) {
                    textout( out, textx, texty, i, f.xmlEscape( new String(caption[i]) ) );
                }
                out.println(" <line class='dash' x1='" + 
                            fx + "' y1='" + line + "' x2='" + tx + "' y2='" + line + "'/>");
            } else {
                for ( int i = 0; i < caption.length; i++ ) {
                    textout( out, textx, texty, i, f.xmlEscape( new String(caption[i]) ) );
                }
                out.println(" <line marker-end='url(#Triangle)' x1='" + 
                            fx + "' y1='" + line + "' x2='" + (tx + (tx > fx ? -arrowx : arrowx)) + "' y2='" + line + "'/>");
            }
        }  // SVG
        
        // OmniGraffle
        else if ( (mode & GRAFFLE) != 0 )
        {
			int linePos = line * GRAFFLE_MULT + GRAFFLE_TOP_MARG;
            int fx = flow.columnOf( from ) * GRAFFLE_MULT;
            int tx = flow.columnOf( to ) * GRAFFLE_MULT;
            int startx = fx < tx ? fx : tx;
            int numColumns = 1;
            if (repeatLabel)
            {
                numColumns = (Math.abs (flow.columnOf( from ) - flow.columnOf( to )) / f.getColumnPitch());
                System.err.println("startx " + startx + "  numColumns " + numColumns);
            }
			
			
			// honor message numbering
            if ( !( from.equals( to ) && (!this.arrowTo && !this.arrowFrom)) ||
                flow.getDoNoteNumbering() )
			{
                int num = flow.nextMessageNumber();
                if ( num != -1 ) {
                    this.myNumber = num;
					String capnum = new String(caption[0]);
                    capnum = num + ". " + capnum;
					caption[0] = capnum.toCharArray();
                }
            }
			
			// group wrapper
			out.println ("<dict>");
			out.println ("<key>Class</key>");
			out.println ("<string>Group</string>");
			out.println ("<key>Graphics</key>");
			out.println ("<array>");
			
            //text
            int textId = id;
            int curX = startx;
            
            double textx = curX;
            //double texty = -1.6 * GRAFFLE_MULT * caption.length + linePos;
            double texty = -1 * GRAFFLE_MULT * caption.length + GRAFFLE_LINE_TXT_OFST + linePos;
            
            for (int i = 0; i < numColumns ; i++)
            {            
                textx =  curX + 10;  //offset for arrow
                
                out.println("<dict>");
                
                out.println ("<key>Bounds</key>");
                out.println ("<string>{{" + textx + ", " + texty + " }, {" + 0 +
                             ", " + 0 + "}}</string>");
                
                out.println("<key>Class</key>");
                out.println("<string>ShapedGraphic</string>");
                
                out.println("<key>FitText</key>");
                out.println("<string>YES</string>");
                
                out.println("<key>ID</key>");
                out.println("<integer>" + id++ + "</integer>");
                
                out.println("<key>Shape</key>");
                out.println("<string>Rectangle</string>");
                
                if ( from.equals( to ) && (!this.arrowTo && !this.arrowFrom))
                {
                    // this is a note
                    out.println("<key>Style</key>");
                    out.println("<dict>");
                    {
                        out.println ("<key>fill</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>Color</key>");
                            out.println ("<dict>");
                            {
                                out.println ("<key>a</key>");
                                out.println ("<string>0.72</string>");
                                out.println ("<key>b</key>");
                                out.println ("<string>0.804798</string>");
                                out.println ("<key>g</key>");
                                out.println ("<string>1</string>");
                                out.println ("<key>r</key>");
                                out.println ("<string>1</string>");
                                out.println ("</dict>");
                            }
                            out.println("</dict>");
                        }
                        
                        out.println("<key>shadow</key>");
                        out.println("<dict>");
                        {
                            out.println ("<key>Color</key>");
                            out.println ("<dict>");
                            {
                                out.println ("<key>a</key>");
                                out.println ("<string>0.21</string>");
                                out.println ("<key>b</key>");
                                out.println ("<string>0</string>");
                                out.println ("<key>g</key>");
                                out.println ("<string>0</string>");
                                out.println ("<key>r</key>");
                                out.println ("<string>0</string>");
                                out.println ("</dict>");
                            }
                            
                            out.println ("<key>Fuzziness</key>");
                            out.println ("<real>9.0033035278320312</real>");
                            
                            out.println ("<key>ShadowVector</key>");
                            out.println ("<string>{0, 2}</string>");
                            
                            out.println("</dict>");
                        }
                        
                        out.println("<key>stroke</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>Cap</key>");
                            out.println ("<integer>0</integer>");
                            
                            out.println ("<key>CornerRadius</key>");
                            out.println ("<real>7</real>");
                            
                            out.println ("<key>Width</key>");
                            out.println ("<string>2</string>");
                            
                            out.println ("<key>Color</key>");
                            out.println ("<dict>");
                            {
                                out.println ("<key>a</key>");
                                out.println ("<string>0.8</string>");
                                out.println ("<key>b</key>");
                                out.println ("<string>0</string>");
                                out.println ("<key>g</key>");
                                out.println ("<string>0.95</string>");
                                out.println ("<key>r</key>");
                                out.println ("<string>0.95</string>");
                                out.println ("</dict>");
                            }
                            
                            out.println ("</dict>");
                        }
                        
                        out.println("</dict>");
                    }                
                }  //note
                else
                {
                    out.println("<key>Style</key>");
                    out.println("<dict>");
                    {
                        out.println ("<key>fill</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>Color</key>");
                            out.println ("<dict>");
                            {
                                out.println ("<key>a</key>");
                                out.println ("<string>0.42</string>");
                                out.println ("<key>b</key>");
                                out.println ("<string>1</string>");
                                out.println ("<key>g</key>");
                                out.println ("<string>1</string>");
                                out.println ("<key>r</key>");
                                out.println ("<string>1</string>");
                                out.println ("</dict>");
                            }
                            out.println("</dict>");
                        }
                        
                        out.println("<key>shadow</key>");
                        out.println("<dict>");
                        {
                            out.println("<key>Draws</key>");
                            out.println("<string>NO</string>");
                            out.println("</dict>");
                        }
                        
                        out.println("<key>stroke</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>Cap</key>");
                            out.println ("<integer>0</integer>");
                            out.println ("<key>CornerRadius</key>");
                            out.println ("<real>7</real>");
                            out.println ("<key>Draws</key>");
                            out.println ("<string>NO</string>");
                            out.println ("</dict>");
                        }
                        
                        out.println("</dict>");
                    }
                    
                }  // not note
                
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
                    int j = 0;
                    for ( j = 0; j < (caption.length - 1); j++ )
                    {
                        out.println(new String (caption[j]) + "\\");
                    }
                    out.println(new String (caption[j]) + "}</string>");
                    out.println("<key>VerticalPad</key>");
                    out.println("<integer>1</integer>");
                    out.println("</dict>");
                }
                
                out.println("</dict>");
                
                curX += f.getColumnPitch() * GRAFFLE_MULT; //move to next column
            }
            // end of text
            
			
			
			// Line
			
            out.println ("<dict>");
            out.println ("<key>Class</key>");
            out.println ("<string>LineGraphic</string>");
            out.println ("<key>ID</key>");
            out.println ("<integer>" + id++ + "</integer>");
            out.println ("<key>Points</key>");
            out.println ("<array>");
            if ( from.equals( to ) && !(!this.arrowTo && !this.arrowFrom))
            {
                // self directed message
                out.println ("<string>{" + fx + ", " + (texty - 5) + "}</string>");
                out.println ("<string>{" + (fx + 20) + ", " + (texty - 10) + "}</string>");
                out.println ("<string>{" + (fx + 30) + ", " + ((texty + linePos) / 2) + "}</string>");
                out.println ("<string>{" + (fx + 20) + ", " + (linePos + 10) + "}</string>");
                out.println ("<string>{" + fx + ", " + (linePos + 5) + "}</string>");
            }
            else
            {
                if ( from.equals( to ) && (!this.arrowTo && !this.arrowFrom))
                {
                    // this is a note
                    out.println ("<string>{" + textx + ", " + texty + "}</string>");
                    out.println ("<string>{" + tx + ", " + linePos + "}</string>");
                }
                else
                {
                    out.println ("<string>{" + fx + ", " + linePos + "}</string>");
                    out.println ("<string>{" + tx + ", " + linePos + "}</string>");
                }
            }
            
            out.println ("</array>");
            
            out.println ("<key>Style</key>");
            out.println ("<dict>");
            {
                if ( from.equals( to ) && (!this.arrowTo && !this.arrowFrom))
                {
                    // line for a note
                    out.println("<key>shadow</key>");
                    out.println("<dict>");
                    {
                        out.println ("<key>Color</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>a</key>");
                            out.println ("<string>0.26</string>");
                            out.println ("<key>b</key>");
                            out.println ("<string>0</string>");
                            out.println ("<key>g</key>");
                            out.println ("<string>0</string>");
                            out.println ("<key>r</key>");
                            out.println ("<string>0</string>");
                            out.println ("</dict>");
                        }
                        
                        out.println ("<key>Fuzziness</key>");
                        out.println ("<real>6</real>");
                        
                        out.println ("<key>ShadowVector</key>");
                        out.println ("<string>{0, 1}</string>");
                        
                        out.println("<key>Draws</key>");
                        out.println("<string>YES</string>");
                        
                        out.println("</dict>");
                    }
                }
                
                out.println ("<key>stroke</key>");
                out.println ("<dict>");
                {
                    out.println ("<key>HeadArrow</key>");
                    if ( this.arrowTo && !this.arrowFrom)
                    {
                        out.println ("<string>FilledArrow</string>");
                        out.println ("<key>HeadScale</key>");
                        out.println ("<real>0.75</real>");
                    }
                    else
                    {
                        out.println ("<string>0</string>");
                        out.println ("<key>HeadScale</key>");
                        out.println ("<real>0.5</real>");
                    }
                    if (!from.equals( to ) && (!this.arrowTo && !this.arrowFrom))
                    {
                        out.println ("<key>Pattern</key>");
                        if (repeatLabel)
                        {
                            // short dash pattern for "--" command
                            out.println ("<integer>2</integer>");
                        }
                        else
                        {
                            // long dash pattern for ".." command
                            out.println ("<integer>1</integer>");
                        }
                    }
                    
                    if ( from.equals( to ) && (!this.arrowTo && !this.arrowFrom))
                    {
                        // line for a note
                        out.println ("<key>Width</key>");
                        out.println ("<string>2</string>");
                        
                        out.println ("<key>Color</key>");
                        out.println ("<dict>");
                        {
                            out.println ("<key>a</key>");
                            out.println ("<string>0.8</string>");
                            out.println ("<key>b</key>");
                            out.println ("<string>0</string>");
                            out.println ("<key>g</key>");
                            out.println ("<string>0.95</string>");
                            out.println ("<key>r</key>");
                            out.println ("<string>0.95</string>");
                            out.println ("</dict>");
                        }
                    }
                    
                    out.println ("<key>TailArrow</key>");
                    if ( this.arrowFrom && !this.arrowTo)
                    {
                        out.println ("<string>FilledArrow</string>");
                        out.println ("<key>TailScale</key>");
                        out.println ("<real>0.75</real>");
                    }
                    else
                    {
                        out.println ("<string>0</string>");
                        out.println ("<key>TailScale</key>");
                        out.println ("<real>0.5</real>");
                    }
                    
                    if ( from.equals( to ) )
                    {
                        out.println ("<key>LineType</key>");
                        out.println ("<integer>1</integer>");
                    }
                    out.println ("</dict>");
                }
                
                out.println ("</dict>");
            }
            
            if ( from.equals( to ) && (!this.arrowTo && !this.arrowFrom))
            {
                // this is a note, link to text box
                out.println ("<key>Tail</key>");
                out.println ("<dict>");
                {
                    out.println ("<key>ID</key>");
                    // id is of text box
                    out.println ("<integer>" + textId + "</integer>");
                    out.println ("</dict>");
                }
            }
            
            out.println("</dict>");			
            
            
			// end group wrapper
			out.println ("</array>");
			out.println ("<key>ID</key>");
			out.println ("<integer>"+ id++ + "</integer>");
			out.println ("</dict>");
			
			
        } else if ( (mode & VML) != 0 ) {
            int Y = (line * f.getVMLYSize()) / f.getTotalHeight();
            int fromX = (flow.columnOf( from ) * f.getVMLXSize()) / f.getTotalWidth();
            int toX = (flow.columnOf( to ) * f.getVMLXSize()) / f.getTotalWidth();
            int startX = VML_TEXT_XOFF + (fromX < toX ? fromX : toX);
            int textOff = VML_TEXT_YOFF;
            
            String xmlCaption = f.xmlEscape( new String( this.caption[0] ) );
            
            // honor message numbering
            if ( !from.equals(to) || flow.getDoNoteNumbering() ) {
                int num = flow.nextMessageNumber();
                if ( num != -1 ) {
                    this.myNumber = num;
                    xmlCaption = "(" + num + ") " + xmlCaption;
                }
            } 
            
            
            // first line
            out.println(" <v:shape fillcolor='black' strokeweight='0pt' coordorigin='0 0' coordsize='100 100' style='position:absolute;top:" +
                        (Y - textOff) + ";left:" + startX + ";width:1;height:1' path = 'm 0,0 l 100,0  e'>");
            
            out.println(" <v:path textpathok='True'/> ");
            out.println(" <v:textpath on='True' string=\"" + 
                        xmlCaption + 
                        "\" " + f.getVMLTextStyle() + " /> ");
            out.println(" </v:shape> ");
            
            // other lines
            for ( int captionIndex = 1; captionIndex < this.caption.length; captionIndex++ ) {
                Y += f.getVMLYSize() / f.getTotalHeight();
                out.println(" <v:shape fillcolor='black' strokeweight='0pt' coordorigin='0 0' coordsize='100 100' style='position:absolute;top:" +
                            (Y - textOff) + ";left:" + startX + ";width:1;height:1' path = 'm 0,0 l 100,0  e'>");
                
                out.println(" <v:path textpathok='True'/> ");
                out.println(" <v:textpath on='True' string=\"" + 
                            f.xmlEscape( new String( this.caption[captionIndex] ) ) +
                            "\" " + f.getVMLTextStyle() + " /> ");
                out.println(" </v:shape> ");
            }
            
            // arrows
            if ( from.equals( to ) ) {
                // nothing to do
            } else if ( !this.arrowFrom && !this.arrowTo ) {
                // dotted line
                out.println(" <v:line from='" + fromX + "," + Y + 
                            "' to='" + toX + "," + Y + "'>");
                out.println("  <v:stroke " + f.getVMLDottedStyle() + "  " + f.getVMLStyle() + " />");
                out.println(" </v:line>");
            } else {
                // regular arrow
                out.println(" <v:line from='" + fromX + "," + Y + 
                            "' to='" + toX + "," + Y + "'>");
                out.println("  <v:stroke   " + f.getVMLStyle() + " " + f.getVMLArrowStyle() + " />");
                out.println(" </v:line>");
            }
        }
    }
}

