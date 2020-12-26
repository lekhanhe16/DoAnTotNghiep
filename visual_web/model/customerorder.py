class CustomerOrder:
    def __init__(self, oid, cus, cart, custimein, ordertime, orderdate):
        self.id = oid
        self.customer = cus
        self.cart = cart
        self.custimein = custimein
        self.ordertime = ordertime
        self.orderdate = orderdate
        self.totalprice = 0
