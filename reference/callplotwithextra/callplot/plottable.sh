#!/bin/sh

HOMEDIR=$(dirname $0)
LIBDIR=${HOMEDIR}/lib

if uname | grep CYGWIN >/dev/null 2>&1
then
    CPATH_SEP=";" 
    LIBDIR=$(cygpath -w $LIBDIR)
else
    CPATH_SEP=":"
fi

style=archtable
links=y

if [ "$1" = "-debug" ]
then
    doing_debug=x
    shift
else
    unset doing_debug
fi

if [ "$1" = "-style" ]
then
    shift
    style=$1
    shift
fi

if [ "$style" = "nolinks" ]
then
    links=n
fi

if [ $# != 1 ]
then
    echo "usage: $0 [-debug] [-style style] {input_file}"
    echo ""
    echo "-debug retains the intermediate files for debugging"
    echo ""
    echo "The annotations can be added by putting "
    echo "one or more lines beginning with ! after the message"
    echo ""
    echo "examples:"
    echo "a->b/MESSAGE"
    echo "!This is a very interesting message"
    echo "!Since it's going from a to b"
    echo ""
    exit 1
fi

xfile=_x_$$.xml
java -jar ${LIBDIR}/callplot.jar -xml $1 >$xfile 

CP="" 
for jar in ${LIBDIR}/xalan.jar ${LIBDIR}/xml-apis.jar ${LIBDIR}/xercesImpl.jar
do
    CP=${CP}${CPATH_SEP}${jar}
done

TMP=xsl$$
java -classpath "${CP}" org.apache.xalan.xslt.Process -IN $xfile -XSL ${LIBDIR}/${style}.xsl -OUT ${TMP} 
cat ${TMP}
rm ${TMP}
if [ -z $doing_debug ]
then
    rm $xfile
else
    echo "retaining xml intermediate file in $xfile" 1>&2
fi

