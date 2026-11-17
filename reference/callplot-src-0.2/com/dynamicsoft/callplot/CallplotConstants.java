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

interface CallplotConstants {
    static final int TEXT	= 0x01;
    static final int PIC 	= 0x02;
    static final int XML	= 0x04;
    static final int VML	= 0x08;
    static final int SVG	= 0x10;
    static final int GRAFFLE	= 0x20;
	
	static final int GRAFFLE_MULT = 14;
	static final int GRAFFLE_TOP_MARG = 15;
    static final int GRAFFLE_LINE_TXT_OFST = -7;

    static final int VML_X_SIZE = 100;

    static final int VML_TEXT_XOFF = 1;
    static final int VML_TEXT_YOFF = 2;

    static final int VML_BOX_PERCENT = 90;
}
