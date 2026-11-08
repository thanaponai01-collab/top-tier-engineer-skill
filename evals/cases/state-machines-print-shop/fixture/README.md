# printshop

Takes print orders, reserves paper for them, prints them on the shop's one printer and ships them.

An order goes draft, checkout (paper is reserved), paid, printing, shipped, archived. A customer can
cancel before printing starts and gets their paper back; a cancelled order that was paid can be
refunded. Unpaid orders are cancelled by the nightly job after a day so their paper is freed.

    python -m printshop list
    python -m printshop nightly
    python -m unittest discover tests
