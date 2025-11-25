from mesa import Agent, Model
from mesa.space import MultiGrid
import random

class SIRAgent(Agent): 
    """ Docstring: 

    """ 
    def __init__(self, unique_id, model, status="S", vaccinated=False):
        super().__init__(model)  # bara model!
        self.unique_id = unique_id  # sätt unik ID själv
        self.status = status        # "S", "I", "R", "D"
        self.vaccinated = vaccinated
        self.days_infected = 0
        self.infector_id = None # Hur många personer den har smittat

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True, # kan gå diagonalt 
            include_center=False # kan inte stanna kvar på samma ställe 
        )
        new_position = self.random.choice(possible_steps) # random steg 
        self.model.grid.move_agent(self, new_position) # uppdaterar position

    def try_infect(self, other):
        if other.status == "S" or other.status == "R": 
            if other.status == "R":
                # Vaccinerade har 3% risk att bli smittade
                infection_chance = 0.03 * 0.19 # Ska vi ta gånger beta? 
            else:
                infection_chance = 1.0 * 0.19 # Ska vi ta gånger beta? 
                
            if self.random.random() < infection_chance:
                other.status = "I" ## Detta leder till att alla som är icke vaccinerade blir sjuka, detta behöver vi ändra
                other.infector_id = self.unique_id # logga vem som smittade
                self.model.log_infection(other) # lägg till i modellens logg 
                

    def step(self):
        if self.status == "D":
            return  # döda rör sig inte eller smittar

        self.move()

        if self.status == "I":
            # Smitta andra i samma cell
            cellmates = self.model.grid.get_cell_list_contents([self.pos])
            for other in cellmates:
                if other != self:
                    self.try_infect(other)

            # Öka dagar sjuk
            self.days_infected += 1

            # Dödsrisk
            if self.random.random() < self.model.mortality_rate:
                self.status = "D"
                return

            # Återhämtning efter 8 dagar
            if self.days_infected >= 8:
                self.status = "R" # Vi antar att man inte kan bli sjuk 2 gånger! 