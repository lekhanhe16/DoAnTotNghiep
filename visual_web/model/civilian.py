from visual_web.model.person import Person


class Civilian(Person):
    def __init__(self, pid, genderobj, ti, di, baseimg, embed, emo, low, high):
        Person.__init__(self, pid)
        self.gender = genderobj
        self.timein = ti
        self.datein = di
        self.faceimg = baseimg
        self.timeout = self.dateout = None
        self.face_embed = embed
        self.expres = []
        self.expres.append(emo)
        self.customer = None
        self.lower = low
        self.higher = high

    def set_time_out(self, to):
        self.timeout = to

    def set_date_out(self, do):
        self.dateout = do
