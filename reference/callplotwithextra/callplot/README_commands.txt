Callplot Commands
=================

Here are the "commands" used in the callplot source files:

opt/name/value          // set option "name" to value "value"

guy/alias/label         // declare an entity with nickname "alias" and label "label"

x->y/Caption            // declare a message from the entity with nickname "x" to 
                        // the entity with nickname "y" with the label "caption"

x->y/cap1/cap2          // declare a message from the entity with nickname "x" to 
                        // the entity with nickname "y" with the label "cap1"
                        // followed by a response in the reverse direction with
                        // caption "cap2"

x..y/Caption            // draw an undirected dotted line from the entity with 
                        // nickname "x" to the entity with nickname "y" with 
                        // the label "caption"

note/x/Text             // Draw the text to the right of the line for entity "x"

The captions and note test can be broken across lines with ^
(caret). In this case, the last line is drawn above the arrow, the
next to last line above that, and so on.

These are the options that exist now:

opt/startLine/{integer}            // initial line # for messages

opt/startColumn/{integer}          // leftmost column for entities

opt/linePitch/{integer}            // # of lines between messages

opt/columnPitch/{integer}          // # of cols between entities

opt/topLabel/{boolean}             // label entities at top?

opt/bottomLabel/{boolean}          // label entities at top?

opt/messageNumbering/{boolean}     // number messages in "(#) text" format?

opt/noteNumbering/{boolean}        // number notes as well as messages?

opt/crunch/{boolean}               // elide lines that would have been just space and 
				   // vertical bars

opt/stagger/{boolean}              // In VML Mode only, stagger the entity-labeling 
				   // to allow wider labels.

opt/vmlStyle/{string}		   // re-define the line style for VML output
default:: Weight='2pt'

opt/vmlArrowStyle/{string}         // re-define the arrow style for VML output
default: EndArrow='Open'

opt/vmlDottedStyle/{string}	   // re-define the dotted line style for VML output
default: DashStyle='dot'

opt/vmlTextStyle/{string}	   // re-define the text style for VML output
default: style='font:normal normal normal 9pt Courier'

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
