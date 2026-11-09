opt/messageNumbering/on
opt/links/on
opt/columnPitch/18
opt/title/Order through a fictional API across many systems
guy/a/Mobile app
guy/b/API gateway
guy/c/Order service
guy/d/Postgres
guy/e/Redis cache
guy/f/Event bus^Kafka
guy/g/AI model^fraud + upsell
guy/h/Payment API^external
guy/i/Warehouse^external
a->b/POST/orders (JWT)
b->b/verify JWT, rate limit
b->c/createOrder(cart)/order id
c->e/GET cart:42/miss
c->d/SELECT cart, prices, stock/rows
c->g/score order risk/risk 0.07
c->d/BEGIN, INSERT order, INSERT items, UPDATE stock/ok
c->h/charge card (idempotency key)/402 declined
c->h/charge card, retry/200 paid
c->d/UPDATE order SET status = PAID/ok
c->f/publish order.paid^async
f->i/order.paid
i->f/ack
i->f/shipment.created^async
f->c/shipment.created
c->d/UPDATE order SET shipment = ...
c->e/DEL cart:42
c->b/201 Created
b->a/201 + order id
note/f/Other consumers get the event:^email, analytics, loyalty points.
