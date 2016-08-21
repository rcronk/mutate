class Animal(object):
    def __init__(self):
        self.kingdom = 'Animal'


class MultiBody(Animal):
    def __init__(self):
        super(Animal, self).__init__()

        self.body_plan = 3

        if self.body_plan == 1:
            self.description = self.kingdom + '-' + 'Brachiopod'
        elif self.body_plan == 2:
            self.description = self.kingdom + '-' + 'Marrella'
        elif self.body_plan == 3:
            self.description = self.kingdom + '-' + 'Trilobite'
        elif self.body_plan == 4:
            self.description = self.kingdom + '-' + 'Hallucigenia'
        else:
            raise Exception('Invalid body plan: %d' % self.body_plan)