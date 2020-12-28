from visual_web.model.person import Person


class Admin(Person):
    def __init__(self, pid, acc, name, role):
        Person.__init__(self, pid)
        self.account = acc
        self.name = name
        self.role = role