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

public class Main implements CallplotConstants {
    
    public static void main( String[] args ) throws Exception {
        int mode = TEXT;
        
        BufferedReader in = null;
        if ( args.length == 0 ) {
            usage();
            System.exit(1);
        }
        for ( int i = 0; i < args.length; i++ ) {
            if ( args[i].equals("-pic") ) {
                mode = PIC;
                continue;
            } else if ( args[i].equals("-xml") ) {
                mode = XML;
                continue;
            } else if ( args[i].equals("-vml") ) {
                mode = VML;
                continue;
            } else if ( args[i].equals("-svg") ) {
                mode = SVG;
                continue;
            } else if ( args[i].equals("-vxml") ) {
                mode = VML | XML;
                continue;
            } else if ( args[i].equals("-graffle") ) {
                mode = GRAFFLE;
                continue;
            } else if ( args[i].equals("-?") || args[i].equals("--help") ) {
                usage();
                System.exit(0);
            } else if ( args[i].equals("-") ) {
                in = new BufferedReader( new InputStreamReader ( System.in ) );
            } else {
                in = new BufferedReader( new FileReader( args[i] ) );
            }
            PrintWriter out = new PrintWriter( System.out );
            Flow.plot( in, out, mode );
            out.flush();
        }
    }
    
    private static void usage() {
        System.err.println("Usage: callplot [-?|--help] [-pic|-vml|-svg|-xml|-graffle] {-|file}");
        System.err.println("");
        System.err.println(" -? --help: print this help");
        System.err.println(" -pic: format output for pic(1), not as ASCII-art.");
        System.err.println(" -svg: format output as Scalable Vector Graphics");
        System.err.println(" -vml: format output as Vector Markup Language for IE and MS Office.");
        System.err.println(" -xml: format output as XML.");
        System.err.println(" -vxml: format output as XML, but with a VML plot.");
        System.err.println(" -graffle: format output as OmniGraffle v5 XML.");
        System.err.println("");
        System.err.println("File Format:");
        System.err.println("opt/name/value          // set option 'name' to value 'value'");
        System.err.println("");
        System.err.println("guy/alias/label         // declare an entity with nickname 'alias' and label 'label'");
        System.err.println("");
        System.err.println("x->y/Caption            // declare a message from the entity with nickname 'x' to ");
        System.err.println("                        // the entity with nickname 'y' with the label 'caption'");
        System.err.println("                        // to include forward slashes, escape them (e.g. '\\/')");
        System.err.println("");
        System.err.println("x->y/cap1/cap2          // declare a message from the entity with nickname 'x' to ");
        System.err.println("                        // the entity with nickname 'y' with the label 'cap1'");
        System.err.println("                        // followed by a response in the reverse direction with");
        System.err.println("                        // caption 'cap2'");
        System.err.println("");
        System.err.println("x..y/Caption            // draw an undirected dotted line from the entity with ");
        System.err.println("                        // nickname 'x' to the entity with nickname 'y' with ");
        System.err.println("                        // the label 'caption'");
        System.err.println("");
        System.err.println("x--y/Caption            // draw an undirected dotted line from the entity with ");
        System.err.println("                        // nickname 'x' to the entity with nickname 'y' with ");
        System.err.println("                        // the label 'caption' shown for each entity line in graffle format");
        System.err.println("");
        System.err.println("note/x/Text             // Draw the text to the right of the line for entity 'x'");
        System.err.println("");
        System.err.println("The captions and note test can be broken across lines with ^");
        System.err.println("(caret). In this case, the last line is drawn above the arrow, the");
        System.err.println("next to last line above that, and so on.");
        System.err.println("");
        System.err.println("These are the options that exist now:");
        System.err.println("");
        System.err.println("opt/startLine/{integer}            // initial line # for messages");
        System.err.println("");
        System.err.println("opt/startColumn/{integer}          // leftmost column for entities");
        System.err.println("");
        System.err.println("opt/linePitch/{integer}            // # of lines between messages");
        System.err.println("");
        System.err.println("opt/columnPitch/{integer}          // # of cols between entities");
        System.err.println("");
        System.err.println("opt/topLabel/{boolean}             // label entities at top?");
        System.err.println("");
        System.err.println("opt/bottomLabel/{boolean}          // label entities at bottom?");
        System.err.println("");
        System.err.println("opt/messageNumbering/{boolean}     // number messages in '(#) text' format?");
        System.err.println("");
        System.err.println("opt/noteNumbering/{boolean}        // number notes as well as messages?");
        System.err.println("");
        System.err.println("opt/crunch/{boolean}               // elide lines that would have been just space and ");
        System.err.println("				   // vertical bars (ascii-art only)");
        System.err.println("opt/stagger/{boolean}               // stagger the boxes to allow longer labels ");
        System.err.println("");
        System.err.println("opt/vmlStyle/{string}		   // re-define the line style for VML output");
        System.err.println("default:: Weight='2pt'");
        System.err.println("");
        System.err.println("opt/vmlArrowStyle/{string}         // re-define the arrow style for VML output");
        System.err.println("default: EndArrow='Open'");
        System.err.println("");
        System.err.println("opt/vmlDottedStyle/{string}	   // re-define the dotted line style for VML output");
        System.err.println("default: DashStyle='dot'");
        System.err.println("");
        System.err.println("opt/vmlTextStyle/{string}	   // re-define the text style for VML output");
        System.err.println("default: style='font:normal normal normal 9pt Courier'");
        System.err.println("");
        System.err.println("opt/vmlBoxStyle/{string}	   // re-define the style applied to the rectangle");
        System.err.println("default: fillcolor='red'	   // at the top of each column ");
        System.err.println("");
        System.err.println("opt/vmlBoxWidthPercentage/{integer} // re-define the %-age of the column filled by ");
        System.err.println("default: 85			    // the rectangle at the top of a column");
        System.err.println("");
        
        System.err.println("boolean options accept 'on', 'true' and 'yes' as meaning true, and their opposites as false.");
        System.err.println("");
    }
}
