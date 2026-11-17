opt/messageNumbering/on
opt/links/on
opt/columnPitch/16
opt/title/How a person uses callplot
guy/e/Engineer
guy/t/Terminal
guy/c/callplot
guy/f/Files
guy/b/Browser
e->f/write calls.msd^guy, arrows, ! comments
e->t/callplot -html calls.msd > calls.html
t->c/run command
c->f/read calls.msd
f->c/text
note/c/parse, layout, draw^diagram + table + links
c->t/one HTML page on stdout
t->f/save calls.html
e->b/open calls.html
b->f/load the file^no server, no network
f->b/self-contained page
b->e/diagram on top, table below
e->b/click badge 7 on the diagram
note/b/jump to row 7^row is highlighted
e->b/click row 7 back link
note/b/scroll diagram to event 7
note/b/The back link is in the left corner of every row^It stays in view when the table scrolls sideways
e->b/switch to side by side^radio switch, no JS
e->t/edit calls.msd, run callplot again
