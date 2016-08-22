class Animal(object):
    def __init__(self):
        self.kingdom = 'Animal'


class MultiBody(Animal):
    def __init__(self):
        Animal.__init__(self)
        self.body_plan = 3

        if self.body_plan == 1:
            self.description = self.kingdom + '-' + 'Body plan 1'
        elif self.body_plan == 2:
            self.description = self.kingdom + '-' + 'Body plan 2'
        elif self.body_plan == 3:
            self.description = self.kingdom + '-' + 'Body plan 3'
        elif self.body_plan == 4:
            self.description = self.kingdom + '-' + 'Body plan 4'
        elif self.body_plan == 5:
            self.description = self.kingdom + '-' + 'Body plan 5'
        elif self.body_plan == 6:
            self.description = self.kingdom + '-' + 'Body plan 6'
        elif self.body_plan == 7:
            self.description = self.kingdom + '-' + 'Body plan 7'
        elif self.body_plan == 8:
            self.description = self.kingdom + '-' + 'Body plan 8'
        elif self.body_plan == 9:
            self.description = self.kingdom + '-' + 'Body plan 9'
        else:
            raise Exception('Invalid body plan: %d' % self.body_plan)
