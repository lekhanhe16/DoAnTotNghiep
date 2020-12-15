class CustomerOrder:
    def __init__(self, oid, cus, cart):
        self.id = oid
        self.customer = cus
        self.cart = cart
        self.totalprice = 0
