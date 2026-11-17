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

public class Flow implements CallplotConstants {
    private LinkedList players;
    private LinkedList messages;
    private Properties opts;

    private int height;
    private int startColumn;
    private int startLine;
    private int guyCaptionLines;
    private int columnPitch;
    private int linePitch;

    private int numPlayers;
    private int numMessages;

    private boolean crunch;
    private boolean stagger;
    private boolean topLabel;
    private boolean bottomLabel;
    private boolean links;

    private String vmlStyle = "";
    private String vmlFont = "";
    private String vmlTextSize = "";
    private String vmlArrowStyle = "";
    private String vmlDotStyle = "";
    private String vmlBoxStyle = "";
    private String vmlTextStyle = "";
    private String vmlBoxTextStyle = "";
    private String vmlBoxWidthPercentage = "";

    private String picXSize = "";
    private String picYSize = "";

    private boolean doNumbering;
    private boolean doNoteNumbering;

    public static void plot( BufferedReader in, PrintWriter out, int mode ) throws IOException {
        Flow f = Parser.parse( in );

        f.layout();
		
        if ( (mode & (PIC | VML | SVG | GRAFFLE)) != 0 ) {
            f.drawPictureOn( out, mode );
        } else {
            f.plotOn( out, mode );
        }
    }

    public Flow( LinkedList players, LinkedList messages, Properties opts ) {
		this.players = players;
		this.messages = messages;
		this.opts = opts;
    }

    private int getIntValueOr( String name, int dflt ) {
		String val = opts.getProperty( name );
		if ( val != null ) {
			return Integer.parseInt( val );
		} else {
			return dflt;
		}
    }

    private boolean getBooleanValueOr( String name, boolean dflt ) {
		String val = opts.getProperty( name );
		if ( val != null ) {
			if ( val.equalsIgnoreCase("yes") ||
				 val.equalsIgnoreCase("true") ||
				 val.equalsIgnoreCase("on") ) {
				return true;
			} else if ( val.equalsIgnoreCase("no") ||
						val.equalsIgnoreCase("false") ||
						val.equalsIgnoreCase("off") ) {
				return false;
			} else {
				throw new RuntimeException("Bad value for boolean option");
			}
		} else {
			return dflt;
		}
    }

    private int getStartLine() { 
		return this.startLine; 
    }

    private int getLinePitch() { 
		return this.linePitch;
    }

    private int getStartColumn() {
		return this.startColumn;
    }

    public int getColumnPitch() {
		return this.columnPitch;
    }

    public int getTotalWidth() {
		return this.numPlayers * this.columnPitch + this.startColumn + this.columnPitch;
    }

    public int getTotalHeight() {
		return this.height;
        //return this.numMessages * this.linePitch + this.startLine + 
	    //(bottomLabel ? this.guyCaptionLines : 0);
    }

    public int getHeaderHeight() {
        return this.guyCaptionLines;
    }

    public int labelLine( int line ) {
		if ( this.topLabel && line < this.guyCaptionLines ) {
			return line;
		} else if ( this.bottomLabel && this.getTotalHeight() - line < this.guyCaptionLines ) {
			return this.guyCaptionLines - 1 - (this.getTotalHeight() - line);
		} else {
			return -1;
		}
    }

    public boolean getDoNumbering() {
		return this.doNumbering;
    }

    public boolean getStagger() {
		return this.stagger;
    }

    public boolean getDoNoteNumbering() {
		return this.doNoteNumbering;
    }

    public String getVMLStyle() {
        return this.vmlStyle;
    }

    public String getVMLArrowStyle() {
        return this.vmlArrowStyle;
    }

    public String getVMLDottedStyle() {
        return this.vmlDotStyle;
    }

    public String getVMLBoxStyle() {
        return this.vmlBoxStyle;
    }

    public String getVMLTextStyle() {
		if ( this.vmlTextStyle.equals("-") ) {
			return "style='FONT-FAMILY:\"" + 
			this.vmlFont +
			"\";FONT-SIZE:" + 
			this.vmlTextSize +
		"pt;V-TEXT-ALIGN:left'";
		} else {
			return this.vmlTextStyle;
		}
    }

    public String getVMLBoxTextStyle() {
		if ( this.vmlBoxTextStyle.equals("-") ) {
			return "style='FONT-FAMILY:\"" + 
			this.vmlFont +
			"\";FONT-SIZE:" + 
			this.vmlTextSize +
		"pt;V-TEXT-ALIGN:center'";
		} else {
			return this.vmlBoxTextStyle;
		}
    }

    public String getVMLBoxWidthPercentage() {
        return this.vmlBoxWidthPercentage;
    }

    private void honorOpts() {
		this.stagger = this.getBooleanValueOr( "stagger", false );

		this.startLine = this.getIntValueOr( "startLine", stagger ? 7 : 4 );
		this.startColumn = this.getIntValueOr( "startColumn", 10 );
		this.linePitch = this.getIntValueOr( "linePitch", 4 );
        if (this.linePitch < 2)
        {
            this.linePitch = 2;
        }
		this.columnPitch = this.getIntValueOr( "columnPitch", 10 );
		this.numPlayers = this.players.size();
		this.numMessages = this.messages.size();

		this.crunch = this.getBooleanValueOr( "crunch", false );
		this.links = this.getBooleanValueOr( "links", true );
		this.topLabel = this.getBooleanValueOr( "topLabel", true );
		this.bottomLabel = this.getBooleanValueOr( "bottomLabel", false );
		this.doNumbering = this.getBooleanValueOr( "messageNumbering", false );
		this.doNoteNumbering = this.getBooleanValueOr( "noteNumbering", false );

        this.picXSize = opts.getProperty( "picXSize", " " );
        this.picYSize = opts.getProperty( "picYSize", " " );

        this.vmlStyle = opts.getProperty( "vmlStyle", " " );
        this.vmlFont = opts.getProperty( "vmlFont", "courier new" );
        this.vmlTextSize = opts.getProperty( "vmlTextSize", "9" );
        this.vmlArrowStyle = opts.getProperty( "vmlArrowStyle", "EndArrow='Open'" );
        this.vmlDotStyle = opts.getProperty( "vmlDottedStyle", "DashStyle='dot'" );
        this.vmlBoxStyle = opts.getProperty( "vmlBoxStyle", "fillcolor='red'" );
        this.vmlTextStyle = opts.getProperty( "vmlTextStyle", "-" );
        this.vmlBoxTextStyle = opts.getProperty( "vmlBoxTextStyle", "-" );
        this.vmlBoxWidthPercentage = opts.getProperty( "vmlBoxWidthPercentage", stagger ? "160" : "90" );
    }

    public void layout() {

		honorOpts();

        this.guyCaptionLines = 0;

		int col = getStartColumn();
		for ( ListIterator li = this.players.listIterator(); li.hasNext(); ) {
			Player p = (Player)li.next();
			p.setColumn( col );
			col += getColumnPitch();
			if ( p.getCaptionLines() > guyCaptionLines ) {
				guyCaptionLines = p.getCaptionLines();
			}
		}

        if ( this.topLabel ) {
            this.startLine += guyCaptionLines;
        }

		int line = getStartLine();
		for ( ListIterator li = this.messages.listIterator(); li.hasNext(); ) {
			Message m = (Message)li.next();
            line += (m.getLength() >= getLinePitch() ? m.getLength() + 1 - getLinePitch() : 0);
			m.setLine( line );
			line += getLinePitch();
		}
		this.height = line;
    }

    public int columnOf( String name ) {
		for ( ListIterator li = this.players.listIterator(); li.hasNext(); ) {
			Player p = (Player)li.next();
			if ( p.getName().equals( name ) ) {
				return p.getColumn();
			}
		}
		throw new IllegalArgumentException( "no player named " + name );
    }

    private int msgNum;

    private void startMessageNumbers() {
		this.msgNum = 1;
    }

    public int nextMessageNumber() {
		if ( this.getDoNumbering() ) {
			return this.msgNum++;
		} else {
			return -1;
		}
    }

    public String xmlEscape( String orig ) {
        return orig;
    }

    public void plot( PrintWriter out, int mode ) {
        if ( (mode & (PIC | VML | SVG)) != 0 ) {
            drawPictureOn( out, mode );
        } else {
            plotOn( out, mode );
        }
    }

    public void plotOn( PrintWriter out, int mode ) {

		startMessageNumbers();

		// do the preamble
		if ( (mode & XML) != 0 ) {
			out.println( "<plot>" );
			out.println( "<picture>" );
			//out.println( "<![CDATA[" );
		}
		
		if ( (mode & GRAFFLE) != 0 ) {
			out.println( "<dict>" );
			out.println( "<key>GraphicsList</key>" );
			out.println( "<array>" );
		}
		
		int width = getTotalWidth();
		char[] lineBuffer = new char[ getTotalWidth() ];
		for ( int line = 0; line <= getTotalHeight(); line++ ) {

			// clear the line buffer
			for ( int i = 0; i < width; i++ ) {
				lineBuffer[i] = ' ';
			}

			// plot all players for this line
			for ( ListIterator li = this.players.listIterator(); li.hasNext(); ) {
				Player p = (Player)li.next();
				p.drawSelf( line, lineBuffer );
			}

			// plot all messages for this line
			for ( ListIterator li = this.messages.listIterator(); li.hasNext(); ) {
				Message m = (Message)li.next();
				m.drawSelf( line, lineBuffer );
			}

			// draw the line
			if ( shouldPrint( lineBuffer ) ) {
				int lastChar = width - 1;
				for ( ; lineBuffer[ lastChar ] == ' ' && lastChar > 0; lastChar-- ) {
				}

				if ( (mode & XML) != 0 ) {
                    int numStart = -1;
                    int num = 1;
                    for ( int i = 0; i <= lastChar ; i++ ) {
                        switch ( lineBuffer[i] ) {
                        case '<':
                            out.write( "&lt;" );
                            break;
                        case '>':
                            out.write( "&gt;" );
                            break;

                        case '(':
                            if ( links ) {
                                numStart = i + 1;

                                while ( i <= lastChar && lineBuffer[i] != ')' ) {
                                    i++;
                                }

                                if ( lineBuffer[i] == ')' ) {
                                    try {
                                        num = Integer.parseInt( new String( lineBuffer, numStart, i - numStart ) );
                                        out.write( "(<a href='#t" + num + "'>" + num + "</a>)<a name='m" + num + "'/>" );
                                        break;
                                    } catch ( NumberFormatException nf ) {
                                    }
                                } 
                        
                                i = numStart - 1;
                            }
                        
                        default:
                            out.write( lineBuffer[i] );
                            break;
                        }
                    }
                } else {
                    out.write( lineBuffer, 0, lastChar + 1 );
                }

				out.println();
			}
		}

		// do the epilogue
		if ( (mode & XML) != 0 ) {
            // close the CDATA thingie
			//out.println( "]]>" );
			out.println( "</picture>" );

			for ( ListIterator li = this.messages.listIterator(); li.hasNext(); ) {
				Message m = (Message)li.next();
				m.printComment( out );
			}

			out.println( "</plot>" );
		}


    }
    
    private int vml_y_size;
    private int vml_x_size;

    public int getVMLYSize() {
        return this.vml_y_size;
    }

    public int getVMLXSize() {
        return this.vml_x_size;
    }

    public boolean shouldPrint( char[] buf ) {
		if ( !crunch ) {
			return true;
		}

		for ( int i = 0; i < buf.length; i++ ) {
			switch ( buf[i] ) {
				case ' ':
				case '|':
					break;
				default:
					return true;
			}
		}
		return false;
    }

    public void drawPictureOn( PrintWriter out, int mode ) {

		startMessageNumbers();

		// do the preamble
		if ( (mode & XML) != 0 ) {
			out.println( "<plot>" );
			out.println( "<picture>" );
		}

        // prologue
        if ( (mode & PIC) != 0 ) {
            out.print( ".PS " + picXSize + " " + picYSize + "\n" );
        } else if ( (mode & SVG) != 0 ) {
            out.println("<?xml version='1.0'?>");
            out.println("<!DOCTYPE svg PUBLIC '-//W3C//DTD SVG 1.0//EN'");
            out.println("'http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd'>");
            this.vml_y_size = getTotalHeight() * 2;
            this.vml_x_size = getTotalWidth();
            int vml_y_pt_size = 432 * vml_y_size / 100;
            int vml_x_pt_size = 432 * vml_x_size / 100;
            out.println("<!-- totalHeight =" + getTotalHeight() + "-->");
            out.println("<!-- totalWidth =" + getTotalWidth() + "-->");
            out.println("<svg width='" + 
                        getTotalWidth()/10 + "in' height='" + getTotalHeight()/6 + 
                        "in' viewBox='0 0 " + getTotalWidth() + " " + 
                        getTotalHeight() + "'>");
            out.println("");
            out.println("  <defs>");
            out.println("    <style type='text/css'><![CDATA[");
            out.println("      rect {");
            out.println("        fill: white;");
            out.println("        stroke: grey;");
            out.println("        stroke-width: 0.1");
            out.println("      }");
            out.println("      text {");
            out.println("        font-size: 1;");
            out.println("      }");
            out.println("      line {");
            out.println("        stroke: black;");
            out.println("        stroke-width: 0.1");
            out.println("      }");
            out.println("      line.dash {");
            out.println("        stroke-dasharray: 1,1;");
            out.println("        stroke: black;");
            out.println("        stroke-width: 0.1");
            out.println("      }");
            out.println("    ]]></style>");
            out.println("    <marker id='Triangle'");
            out.println("      viewBox='0 0 10 10' refX='0' refY='5' ");
            out.println("      markerUnits='strokeWidth'");
            out.println("      markerWidth='4' markerHeight='3'");
            out.println("      orient='auto'>");
            out.println("      <path d='M 0 0 L 10 5 L 0 10 z' />");
            out.println("    </marker>");
            out.println("    <filter id='dropShadow' x='-.1' y='-.1' width='200' height='120'>");
            out.println("       <feOffset in='SourceGraphic' dx='0' dy='0' result='orig' />");
            out.println("       <feGaussianBlur in='SourceAlpha' stdDeviation='.3' result='shadow' />");
            out.println("       <feOffset in='shadow' dx='0' dy='.1' result='movedShadow' />");
            out.println("       <feMerge>");
            out.println("           <feMergeNode in='movedShadow' />");
            out.println("           <feMergeNode in='orig' />");
            out.println("       </feMerge>");
            out.println("    </filter>");
            out.println("  </defs>");
        } else if ( (mode & VML) != 0 ) {
            out.println("<html xmlns:v='urn:schemas-microsoft-com:vml'");
            out.println("xmlns='http://www.w3.org/TR/REC-html40'>");
            out.println("");
            out.println("<head>");
            out.println("");
            out.println("<!--[if !mso]>");
            out.println("<style>");
            out.println("v\\:* {behavior:url(#default#VML);}");
            out.println(".shape {behavior:url(#default#VML);}");
            out.println("</style>");
            out.println("<![endif]-->");
            out.println("");
            out.println("</head>");
            out.println("");
            out.println("<body>");
            this.vml_y_size = getTotalHeight() * 2;
            this.vml_x_size = getTotalWidth();
            int vml_y_pt_size = 432 * vml_y_size / 100;
            int vml_x_pt_size = 432 * vml_x_size / 100;
            out.println("<!-- totalHeight =" + getTotalHeight() + "-->");
            out.println("<!-- totalWidth =" + getTotalWidth() + "-->");
            out.println("<v:group style='position:relative;left:1pt;top:2pt;width:" + 
                        vml_x_pt_size + "pt;height:" + vml_y_pt_size + 
                        "pt;' coordsize='" + vml_x_size + "," + vml_y_size + "' >");
            out.println("");
        } else if ( (mode & GRAFFLE) != 0 ) {
            out.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
            out.println("<!DOCTYPE plist PUBLIC \"-//Apple Computer//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">");
			out.println("<plist version=\"1.0\">");
			out.println("<dict>");
			out.println("<key>GraphicsList</key>");
            out.println("<array>");
			
			this.vml_y_size = getTotalHeight();
            this.vml_x_size = getTotalWidth();
            
            for ( ListIterator li = this.messages.listIterator(); li.hasNext(); ) {
                Message m = (Message)li.next();
                m.drawPictureOn( this, out, mode );
            }
            
            for ( ListIterator li = this.players.listIterator(); li.hasNext(); ) {
                Player p = (Player)li.next();
                p.drawPictureOn( this, out, mode );
            }
        }

        if ( (mode & GRAFFLE) == 0 ) {
            for ( ListIterator li = this.players.listIterator(); li.hasNext(); ) {
                Player p = (Player)li.next();
                p.drawPictureOn( this, out, mode );
            }
            
            for ( ListIterator li = this.messages.listIterator(); li.hasNext(); ) {
                Message m = (Message)li.next();
                m.drawPictureOn( this, out, mode );
            }
        }
        
        // epilogue
        if ( (mode & PIC) != 0 ) {
            out.println( ".PE\n" );
        } else if ( (mode & SVG) != 0 ) {
            out.println("</svg>");
        } else if ( (mode & VML) != 0 ) {
            out.println("");
            out.println("</v:group>");
            out.println("</body>");
            out.println("</html>   ");
        } else if ( (mode & GRAFFLE) != 0 ) {
            out.println("</array>");
            out.println("</dict>");
            out.println("</plist>");
			
			if ( (mode & XML) != 0 ) {
				out.println( "</picture>" );

				for ( ListIterator li = this.messages.listIterator(); li.hasNext(); ) {
					Message m = (Message)li.next();
					m.printComment( out );
				}

				out.println( "</plot>" );
			}
		}
	}
}
