from mesa import Agent, Model
from mesa.space import MultiGrid
import random

class SIRAgent(Agent): 
    """ Class för Agenterna:  
    """ 
    new_infected = 0
    def __init__(self, unique_id, model, status="S", vaccinated=False):
        """ Initierar SIR agent objects. 

        """
        super().__init__(model)  # bara model!
        self.unique_id = unique_id  # sätt unik ID själv
        self.status = status        # "S", "I", "R", "D"
        self.vaccinated = vaccinated
        self.days_infected = 0
        self.infector_id = None # Hur många personer den har smittat

    def move(self):
        """ Definierar move funktionen 
        - ser till att agenten uppdaterar sin position. 
        
        """
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True, # kan gå diagonalt 
            include_center=False # kan inte stanna kvar på samma ställe 
        )
        new_position = self.random.choice(possible_steps) # random steg 
        self.model.grid.move_agent(self, new_position) # uppdaterar position

    def try_infect(self, other):
        """ Definierar funktion för att infektera andra om 
        agenten är infekterad. 

        """
        if other.status == "S" or other.status == "R": 
            if other.status == "R":
                # Vaccinerade har 3% risk att bli smittade
                infection_chance = 0.03 * 0.19 # Ska vi ta gånger beta? räkna om Beta sen
            else:
                infection_chance = 1.0 * 0.19 # Ska vi ta gånger beta? Räkna om beta sen 
                
            if self.random.random() < infection_chance:
                other.status = "I" ## Detta leder till att alla som är icke vaccinerade blir sjuka, detta behöver vi ändra
                other.infector_id = self.unique_id # logga vem som smittade (du sparar att jag har smittat dig) 
                self.model.log_infection(other) # lägg till i modellens logg

                SIRAgent.new_infected += 1

    def get_new_infected(self):
        return SIRAgent.new_infected

    def reset_new_infected(self):
        SIRAgent.new_infected = 0
                

    def step(self):
        """ Definierar funktion för vad som händer när ett steg tas. 
        Olika beroende på vilken status - dvs S, I, R eller D, agenten har. 
        Kallar på move funktionen om agenten ej är död. 
        Om ej död initeras eventuellt infektering, dödsrisk checkas 
        och ökat antalet dagar sjuk och återhämtning uppdateras. 

        """ 
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