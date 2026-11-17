BEGIN {
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    letidx = 1;
    t0 = "";
    t = "";
    print "opt/messageNumbering/on";
    print "opt/xml/on";
    print "opt/crunch/on";
    if ( LINKS == "y" ) {
	print "opt/links/on";
    } else {
	print "opt/links/off";
    }
    os = od = "";
}

{
    sub("\r","",$0);
}

$1 == "@" {
    sub("\r","",$3);
    ALIAS[$2] = $3;
    if ( ! ( $3 in GUYS ) ) {
	 print ( "guy/" $3 "/" $3 );
	 GUYS[$3] = $3;
	 print "["$3"] going into guys">>"debug";
    }
    next;
}

/^@/ {
     print substr($0,2);
     next;
}

/^----/ { 
     next;
}

/^Date [0-9][0-9]\/[0-9][0-9]\/[0-9][0-9][0-9][0-9]/ { 
     lt = t;
     t = $0; 

     if ( t0 == "" ) 
	  t0 = t;

     gsub("&","\\&amp;");
     gsub("<","\\&lt;");
     gsub(">","\\&gt;");
     mDate = "!!" $0;

     next; 
}

/^[0-9][0-9]\/[0-9][0-9]\/[0-9][0-9][0-9][0-9]/ { 
     lt = t;
     t = $0; 

     if ( t0 == "" ) 
	  t0 = t;

     gsub("&","\\&amp;");
     gsub("<","\\&lt;");
     gsub(">","\\&gt;");
     mDate = "!!" $0;

     next; 
}

/^Source Address/ { 
    s = $3; 
    sub("\r","",s);
    if ( s in ALIAS ) 
	s = ALIAS[s]; 
    if ( ! ( s in GUYS ) ) {
     print "["s"] not in guys">>"debug"
	letr = substr(letters,letidx,1);
	print ( "guy/" letr "/" s );
	GUYS[s] = letr;
	letidx++;
    }
    s = GUYS[s];

    gsub("&","\\&amp;");
    gsub("<","\\&lt;");
    gsub(">","\\&gt;");
    mSrc = "!!" $0;

    next; 
}

/^Destination Address/ { 
    d = $3; 
    sub("\r","",d);
    if ( d in ALIAS ) 
	d = ALIAS[d];
    if ( ! ( d in GUYS ) ) {
     print "["d"] not in guys">>"debug"
	letr = substr(letters,letidx,1);
	print ( "guy/" letr "/" d );
	GUYS[d] = letr;
	letidx++;
    }
    d = GUYS[d];

    gsub("&","\\&amp;");
    gsub("<","\\&lt;");
    gsub(">","\\&gt;");
    mDest = "!!" $0;

    next;
}

$1 ~ "^(MESSAGE|INVITE|BYE|CANCEL|REGISTER|INFO|NOTIFY|SUBSCRIBE|PUBLISH)" { 
    print s "->" d "/" $1;
    print mDate;
tdiff( t, t0, "initial" );
tdiff( t, lt, "last" );
    if ( length(s) > 1 ) 
	print mSrc " (" s ")";
    else
	print mSrc;
    if ( length(s) > 1 ) 
	print mDest " (" d ")";
    else 
	print mDest " (" d ")";
}

$1 ~ "^(GET|POST)" { 
    print s "->" d "/" $1;
    print mDate;
tdiff( t, t0, "initial" );
tdiff( t, lt, "last" );
    if ( length(s) > 1 ) 
	print mSrc " (" s ")";
    else
	print mSrc;
    if ( length(s) > 1 ) 
	print mDest " (" d ")";
    else 
	print mDest " (" d ")";
}

/^SIP\/2.0 / { 
    line = $0;
    sub($1" ","",line); 
    print s "->" d "/" line;
    print mDate;
tdiff( t, t0, "initial" );
tdiff( t, lt, "last" );
    if ( length(s) > 1 ) 
	print mSrc " (" s ")";
    else
	print mSrc;
    if ( length(s) > 1 ) 
	print mDest " (" d ")";
    else 
	print mDest " (" d ")";
}

/^HTTP\/1.. / { 
    line = $0;
    sub($1" ","",line); 
    print s "->" d "/" line;
    print mDate;
tdiff( t, t0, "initial" );
tdiff( t, lt, "last" );
    if ( length(s) > 1 ) 
	print mSrc " (" s ")";
    else
	print mSrc;
    if ( length(s) > 1 ) 
	print mDest " (" d ")";
    else 
	print mDest " (" d ")";
}

#
# These rules propagate the leading -,
# used to omit a packet from the flow
#
$1 ~ "^-(MESSAGE|INVITE|BYE|CANCEL|REGISTER|INFO|NOTIFY|SUBSCRIBE|PUBLISH)" { 
    print "-" s "->" d "/" substr($1,2);
}

$1 ~ "^-(GET|POST)" { 
    print "-" s "->" d "/" substr($1,2);
}

/^-SIP\/2.0 / { 
    line = $0;
    sub($1" ","",line); 
    print "-" s "->" d "/" line;
}

/^-HTTP\/1.. / { 
    line = $0;
    sub($1" ","",line); 
    print "-" s "->" d "/" line;
}

{ 
    gsub("&","\\&amp;");
    gsub("<","\\&lt;");
    gsub(">","\\&gt;");
    print "!" $0;
}

function tdiff( a, b, when ) {
     at = toTime(a);
     bt = toTime(b);
     if ( bt != "" ) print "!!    "at - bt " from " when ;
}

function toTime( ts ) {
     gsub( "[/, .]", ":", ts );
     n = split( ts, arr, ":" );
     return arr[n] / 1000 + arr[n-1] + 60 * arr[n-2] + 3600 * arr[n-3];
}
