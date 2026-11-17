Using callplot and plottable
============================

Dave Ladd's 'callplot' Java program is a crude text-based message sequence diagram tool.
It is best used to produce ASCII art, though it can theoretically spit out other graphics.

The tool can be used by itself, or from the 'plottable' shell script, which supports
annotations that are summarized in a table after the diagram, and hyperlinked to the
diagram as well. The table layout is generated from an XSLT script that can be customized.

Callplot usage
--------------

Usage:

java -jar callplot.jar [-pic|-vml|-xml] {file..}

file "-" means standard input.  

The -pic option produces pic(1) format output, rather than the default
ASCII Art.  Note that the pic support is pretty rudimentary at the
moment.

The -vml option creates output in Vector Markup Language, which is
understood by Internet Explorer and Microsoft Office.

The -xml option creates output in a hybrid ascii-art/annotations XML
format that is designed to be used for annotated call flows.

The "commands" are documented in README_commands.txt.

Plottable usage
---------------

The annotated-ping-pong version of callplot takes augmented message sequence
descriptions as input, and produces HTML documents with a message sequence
diagram followed by a table. It invokes callplot with default ASCII art
diagram type (change the script if you want something else!).

The plottable shell script should run under *nix, including cygwin,
provided a recent-ish java executable is in your path.

Usage is as follows:

$ ./plottable.sh [-style style] myflow.msd > myflow.html

where 'style' is the name of the XSLT script used to lay out the document and table.
(Current default is archtable.)

2. Quick Start

In the default layout, lines from the input file of the form "! packet" appear in the
third column of the table in a constant-width font.

Lines of the form "!! note" are inserted into the 2nd column of the
table for the "current" message. The "current" message is defined as the most recent message line in the document. 


3. Caveats

Annotating the messages makes it difficult to use the multiple-message
forms (e.g. a->b/Mesg/Mesg/Mesg).

For now, XML-significant characters in comment text need to be escaped:

 <  -> &lt;
 >  -> &gt;
 &  -> &amp;
