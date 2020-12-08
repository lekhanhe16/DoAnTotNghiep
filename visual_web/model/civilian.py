from visual_web.model.person import Person


class Civilian(Person, object, object):
    def __init__(self, pid, ageobj, genderobj):
        Person.__init__(self, pid)
        self.age = ageobj
        self.gender = genderobj
