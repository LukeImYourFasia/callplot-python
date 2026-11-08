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

public class Parser {
    
    public static Flow parse( BufferedReader in ) throws IOException {
        LinkedList guys = new LinkedList();
        LinkedList msgs = new LinkedList();
        Properties opts = new Properties();
        
        Flow f = new Flow( guys, msgs, opts );
        Message lastMsg = null;
        boolean dummy = false;
        boolean newDummy = false;
        for ( ;; )
        {
            String line = in.readLine();
            if ( line == null )
            {
                break;
            }
            
            String tLine = line.trim();
            
            if ( tLine.startsWith("#") || tLine.length() == 0 ) {
                continue;
            }
            
            if ( tLine.startsWith("!!") ) {
                lastMsg.addNote( tLine.substring(2) );
                continue;
            } else if ( tLine.startsWith("!") ) {
                lastMsg.addComment( tLine.substring(1) );
                continue;
            }
            
            
            if ( tLine.startsWith("-") ) {
                newDummy = true;
                line = line.substring(1);
            }
            
            // split the line up between any non-escaped slashes
            String[] splitLineEscaped = line.split("(?<=[^\\\\])\\/");
            int tkn = 0;
            // remove escapes on slashes, skip command field
            String[] splitLine = new String[splitLineEscaped.length];
            splitLine[0] = splitLineEscaped[0];
            for (int i = 1; i < splitLineEscaped.length; i++)
            {
                splitLine[i] = splitLineEscaped[i].replaceAll("\\\\\\/", "/");
            }
            
            String command = splitLine[tkn++];            
            if ( command.equals("guy") )
            {
                guys.add( new Player( f, splitLine[tkn++], splitLine[tkn++] ) );
            }
            else if ( command.equals("note") )
            {
                String from = splitLine[tkn++];
                if ( ! dummy && lastMsg != null )
                {
                    msgs.add( lastMsg );
                }
                dummy = newDummy;
                newDummy = false;
                lastMsg = new Message( f, from, from, splitLine[tkn++], ' ', false, false, null );
            }
            else if ( command.equals("opt") )
            {
                String name = splitLine[tkn++];
                String value = splitLine[tkn++];
                opts.put( name, value );
            }
            else if ( command.indexOf("->") != -1 )
            {
                // must be a message
                int arrowIdx = command.indexOf( "->" );
                String from = command.substring( 0, arrowIdx ).trim();
                String to = command.substring( arrowIdx + 2 ).trim();
                boolean reply = false;
                while ( tkn < splitLine.length )
                {
                    if ( ! dummy && lastMsg != null )
                    {
                        msgs.add( lastMsg );
                    }
                    dummy = newDummy;
                    newDummy = false;
                    if ( reply )
                    {
                        lastMsg = new Message( f, to, from, splitLine[tkn++], '-', false, true, null );
                    }
                    else
                    {
                        lastMsg = new Message( f, from, to, splitLine[tkn++], '-', false, true, null );
                    }
                    reply = !reply;
                }
            }
            else if ( command.indexOf("..") != -1 )
            {
                int dotIdx = command.indexOf( ".." );
                String from = command.substring( 0, dotIdx ).trim();
                String to = command.substring( dotIdx + 2 ).trim();
                if ( ! dummy && lastMsg != null )
                {
                    msgs.add( lastMsg );
                }
                dummy = newDummy; 
                newDummy = false;
                lastMsg = new Message( f, from, to, splitLine[tkn++], '.', false, false, null );
            }
            else if ( command.indexOf("--") != -1 )
            {
                // dots like above, but put label by each entity line
                int dotIdx = command.indexOf( "--" );
                String from = command.substring( 0, dotIdx ).trim();
                String to = command.substring( dotIdx + 2 ).trim();
                if ( ! dummy && lastMsg != null )
                {
                    msgs.add( lastMsg );
                }
                dummy = newDummy; 
                newDummy = false;
                lastMsg = new Message( f, from, to, splitLine[tkn++], '.', false, false, null, true );
            }
        }
        if ( ! dummy && lastMsg != null )
        {
            msgs.add( lastMsg );
        }
        return f;
    } 
}
