usage:

callplot.sh [-pic|-vml|-xml|-svg|-graffle] {file..}

file "-" means standard input.  

The -pic option produces pic(1) format output, rather than the default
ASCII Art.  Note that the pic support is pretty rudimentary at the
moment.

The -vml option creates output in Vector Markup Language, which is
understood by Internet Explorer and Microsoft Office.

The -xml option creates output in a hybrid ascii-art/annotations XML
format that is designed to be used for annotated call flows.

The -graffle option creates output in OmniGraffle(TM) version 5 format.

Here are the "commands":

opt/name/value          // set option "name" to value "value"

guy/alias/label         // declare an entity with nickname "alias" and label "label"

x->y/Caption            // declare a message from the entity with nickname "x" to 
                        // the entity with nickname "y" with the label "caption"
						// When using --graffle, x->x can be used to show a looped
						// back message

x->y/cap1/cap2          // declare a message from the entity with nickname "x" to 
                        // the entity with nickname "y" with the label "cap1"
                        // followed by a response in the reverse direction with
                        // caption "cap2"

x..y/Caption            // draw an undirected dotted line from the entity with 
                        // nickname "x" to the entity with nickname "y" with 
                        // the label "caption"

x--y/Caption            // draw an undirected dotted line from the entity with 
                        // nickname 'x' to the entity with nickname 'y' with 
                        // the label 'caption' shown for each entity line in graffle format


note/x/Text             // Draw the text to the right of the line for entity "x"

The captions and note test can be broken across lines with ^
(caret). In this case, the last line is drawn above the arrow, the
next to last line above that, and so on.

Forward slashes can be added to the captions by using a back slash in
front of them.  For example:

note/actor1/GET home\/away\/from\/home

Will display as:

home/away/from/home


Options are specified with opt/ followed by the option name and the value:

opt/startLine/{integer}            // initial line # for messages

opt/startColumn/{integer}          // leftmost column for entities

opt/linePitch/{integer}            // # of lines between messages

opt/columnPitch/{integer}          // # of cols between entities

opt/topLabel/{boolean}             // label entities at top?

opt/bottomLabel/{boolean}          // label entities at bottom?

opt/messageNumbering/{boolean}     // number messages in "(#) text" format?

opt/noteNumbering/{boolean}        // number notes as well as messages?

opt/crunch/{boolean}               // elide lines that would have been just space and 
				   // vertical bars

opt/stagger/{boolean}              // In VML Mode only, stagger the entity-labeling 
				   // to allow wider labels.

opt/vmlFont/{string}		   // re-define the font for VML text
default:: courier

opt/vmlTextSize/{string}	   // re-define the point size for VML text
default:: 9

opt/vmlStyle/{string}		   // re-define the line style for VML output
default:: <empty>

opt/vmlArrowStyle/{string}         // re-define the arrow style for VML output
default: EndArrow='Open'

opt/vmlDottedStyle/{string}	   // re-define the dotted line style for VML output
default: DashStyle='dot'

opt/vmlTextStyle/{string}	   // re-define the text style for VML output
default: style='FONT-FAMILY:"{vmlFont}";FONT-SIZE:{vmlTextSize}pt;v-text-align=left'
				   // Note that while the default string includes the
				   // current font and size values, a value
				   // for this option is taken literally


opt/vmlBoxTextStyle/{string}	   // re-define the text style in the header boxes
default: style='FONT-FAMILY:"{vmlFont}";FONT-SIZE:{vmlTextSize}pt;v-text-align=center
				   // Note that while the default string includes the
				   // current font and size values, a value
				   // for this option is taken literally


opt/vmlBoxStyle/{string}	   // re-define the style applied to the rectangle
default: fillcolor='red'	   // at the top of each column 

opt/vmlBoxWidthPercentage/{integer} // re-define the %-age of the column filled by 
default: 85			    // the rectangle at the top of a column



boolean options accept "on", "true" and "yes" as meaning true, and
their opposites as false.

Here's a simple example:

--- input ---
opt/columnPitch/15
guy/f/Fred
guy/b/Barney
f->b/Please
note/b/Gives bowling ball
b->f/Stuff
b..f/RTP
f->b/Thank You
b->f/You're Welcome
-------------

--- output ---
        Fred          Barney                           
          |              |                             
          |              |                             
          |Please        |                             
          |------------->|                             
          |              |                             
          |              |                             
          |              |Gives bowling ball           
          |              |                             
          |              |                             
          |              |                             
          |Stuff         |                             
          |<-------------|                             
          |              |                             
          |              |                             
          |RTP           |                             
          |..............|                             
          |              |                             
          |              |                             
          |Thank You     |                             
          |------------->|                             
          |              |                             
          |              |                             
          |You're Welcome|                             
          |<-------------|                             
          |              |                             
          |              |                             
          |              |                             
          |              |                             
-------------


and a more complex example:

--- input ---
opt/linePitch/2
opt/messageNumbering/on
opt/topLabel/off
opt/bottomLabel/on
guy/c/Caller
guy/g/GW
guy/a/AS
guy/m/MS
guy/h/Web
guy/r/RADIUS
guy/e/Callee
c->g/Call #
g->a/INVITE SDP A/183 Trying
a->m/INVITE SDP A
m->h/HTTP GET/200 OK (VXML)
m->a/200 OK SDP B
a->g/200 OK SDP B
g->a/ACK
a->m/ACK
g..m/RTP
m->h/HTTP POST/200 OK
h->r/Authorize/Balance
m->h/HTTP POST/200 OK
h->r/Callee Number/Time Remaining
g..m/Music
a->e/INVITE/200 OK
a->g/INVITE/200 OK
a->m/BYE/200 OK
a->g/ACK
a->e/ACK
g..e/PHONE CALL
a->m/INVITE
m->h/HTTP GET/200 OK (VXML)
m->a/200 OK
a->e/INVITE (hold)/200 OK
a->g/INVITE/200 OK
a->m/ACK
a->g/ACK
m..g/Time Warning
m->a/BYE/200 OK
a->e/INVITE/200 OK
a->g/INVITE/200 OK
a->e/ACK
a->g/ACK
g..e/PHONE CALL
a->m/INVITE
m->h/HTTP GET/200 OK (VXML)
m->a/200 OK
a->e/BYE/200 OK
a->g/INVITE/200 OK
a->g/ACK
m..g/Post-call Announcement
a->g/BYE/200 OK
-------------
--- output ---
          |         |         |         |         |         |         |                   
          |         |         |         |         |         |         |                   
          |         |         |         |         |         |         |                   
          |(1) Call #         |         |         |         |         |                   
          |-------->|         |         |         |         |         |                   
          |         |(2) INVITE SDP A   |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |(3) 183 Trying     |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |         |(4) INVITE SDP A   |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |         |         |(5) HTTP GET       |         |                   
          |         |         |         |-------->|         |         |                   
          |         |         |         |(6) 200 OK (VXML)  |         |                   
          |         |         |         |<--------|         |         |                   
          |         |         |(7) 200 OK SDP B   |         |         |                   
          |         |         |<--------|         |         |         |                   
          |         |(8) 200 OK SDP B   |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(9) ACK  |         |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |         |(10) ACK |         |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |(11) RTP |         |         |         |         |                   
          |         |...................|         |         |         |                   
          |         |         |         |(12) HTTP POST     |         |                   
          |         |         |         |-------->|         |         |                   
          |         |         |         |(13) 200 OK        |         |                   
          |         |         |         |<--------|         |         |                   
          |         |         |         |         |(14) Authorize     |                   
          |         |         |         |         |-------->|         |                   
          |         |         |         |         |(15) Balance       |                   
          |         |         |         |         |<--------|         |                   
          |         |         |         |(16) HTTP POST     |         |                   
          |         |         |         |-------->|         |         |                   
          |         |         |         |(17) 200 OK        |         |                   
          |         |         |         |<--------|         |         |                   
          |         |         |         |         |(18) Callee Number |                   
          |         |         |         |         |-------->|         |                   
          |         |         |         |         |(19) Time Remaining|                   
          |         |         |         |         |<--------|         |                   
          |         |(20) Music         |         |         |         |                   
          |         |...................|         |         |         |                   
          |         |         |(21) INVITE        |         |         |                   
          |         |         |-------------------------------------->|                   
          |         |         |(22) 200 OK        |         |         |                   
          |         |         |<--------------------------------------|                   
          |         |(23) INVITE        |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(24) 200 OK        |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |         |(25) BYE |         |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |         |(26) 200 OK        |         |         |                   
          |         |         |<--------|         |         |         |                   
          |         |(27) ACK |         |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |         |(28) ACK |         |         |         |                   
          |         |         |-------------------------------------->|                   
          |         |(29) PHONE CALL    |         |         |         |                   
          |         |.................................................|                   
          |         |         |(30) INVITE        |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |         |         |(31) HTTP GET      |         |                   
          |         |         |         |-------->|         |         |                   
          |         |         |         |(32) 200 OK (VXML) |         |                   
          |         |         |         |<--------|         |         |                   
          |         |         |(33) 200 OK        |         |         |                   
          |         |         |<--------|         |         |         |                   
          |         |         |(34) INVITE (hold) |         |         |                   
          |         |         |-------------------------------------->|                   
          |         |         |(35) 200 OK        |         |         |                   
          |         |         |<--------------------------------------|                   
          |         |(36) INVITE        |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(37) 200 OK        |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |         |(38) ACK |         |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |(39) ACK |         |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(40) Time Warning  |         |         |         |                   
          |         |...................|         |         |         |                   
          |         |         |(41) BYE |         |         |         |                   
          |         |         |<--------|         |         |         |                   
          |         |         |(42) 200 OK        |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |         |(43) INVITE        |         |         |                   
          |         |         |-------------------------------------->|                   
          |         |         |(44) 200 OK        |         |         |                   
          |         |         |<--------------------------------------|                   
          |         |(45) INVITE        |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(46) 200 OK        |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |         |(47) ACK |         |         |         |                   
          |         |         |-------------------------------------->|                   
          |         |(48) ACK |         |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(49) PHONE CALL    |         |         |         |                   
          |         |.................................................|                   
          |         |         |(50) INVITE        |         |         |                   
          |         |         |-------->|         |         |         |                   
          |         |         |         |(51) HTTP GET      |         |                   
          |         |         |         |-------->|         |         |                   
          |         |         |         |(52) 200 OK (VXML) |         |                   
          |         |         |         |<--------|         |         |                   
          |         |         |(53) 200 OK        |         |         |                   
          |         |         |<--------|         |         |         |                   
          |         |         |(54) BYE |         |         |         |                   
          |         |         |-------------------------------------->|                   
          |         |         |(55) 200 OK        |         |         |                   
          |         |         |<--------------------------------------|                   
          |         |(56) INVITE        |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(57) 200 OK        |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |(58) ACK |         |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(59) Post-call Announcement  |         |         |                   
          |         |...................|         |         |         |                   
          |         |(60) BYE |         |         |         |         |                   
          |         |<--------|         |         |         |         |                   
          |         |(61) 200 OK        |         |         |         |                   
          |         |-------->|         |         |         |         |                   
          |         |         |         |         |         |         |                   
       Caller      GW        AS        MS        Web     RADIUS    Callee     
--------------


Release Information:

0.1
	-baseline release
	
0.2
	-OmniGraffle(TM) output support
	-loop back message
	-lines with captions in each column
	-forward slash in captions
	-various formatting fixes in output

