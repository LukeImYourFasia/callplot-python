opt/messageNumbering/on
opt/links/on
opt/columnPitch/17
opt/title/One callplot run through all modules
guy/u/User^shell
guy/c/bin
guy/r/render()^index.js
guy/p/parser.js
guy/f/flow.js^Flow + layout
guy/h/render
guy/i/ir.js^IR
guy/o/html
guy/j/jcompat.js
u->c/callplot -svg fred > fred.svg
c->c/scan flags (Java rules)^pick mode + options
c->c/read file bytes (fs)^decode as UTF-8
c->r/render(text, mode, ctx, options)
r->p/parse(text)
p->j/javaTrim, javaSplit/clean tokens
p->r/Flow with players[], messages[]
r->f/layout(): options, columns, numbering
f->j/fmtD, idiv, parseJavaInt/Java-exact numbers
f->r/positions and widths ready
note/r/Compatible outputs read Flow.^New outputs read the IR.
r->h/draw(Flow, ctx)^static switch on mode
h->h/text, pic, svg, vml, graffle, table
h->r/string
r->i/buildModel(Flow)^only for -mermaid, -plantuml, -html
i->o/events e1..eN + srcLine
o->r/string
r->c/output string
c->u/stdout bytes, exit code 0
