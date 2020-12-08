from visual_web.model.person import Person


class Admin(Person, object):
    def __init__(self, pid, acc):
        Person.__init__(self, pid)
        self.account = acc
