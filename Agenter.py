from mesa import Agent, Model
from mesa.space import MultiGrid
import random

class SIRAgent(Agent): 
    """
    Agentklass för ett SIR-system i en smittspridningsmodell.

    Syfte:
        Representerar en individ som kan röra sig, infektera andra,
        samt byta status mellan S (susceptible), I (infected),
        R (recovered) och D (dead).

    Input:
        unique_id (int): Unikt ID för agenten.
        model (mesa.Model): Modellinstans som agenten tillhör.
        status (str): Initial hälsostatus ("S", "I", "R" eller "D"). Default="S".
        vaccinated (bool): Om agenten är vaccinerad. Påverkar infektionstrolighet.

    Output:
        En instans av SIRAgent.
    """
    
    new_infected = 0
    
    def __init__(self, unique_id, model, status="S", vaccinated=False):
       """
        Syfte:
            Initierar en SIR-agent med status, vaccinationstillstånd och trackar
            infektionstillstånd över tid.

        Input:
            unique_id (int): Agentens unika ID.
            model (Model): Modellen agenten tillhör.
            status (str): Startstatus ("S", "I", "R", "D").
            vaccinated (bool): Om agenten är vaccinerad.

        Output:
            Inga direkta return-värden. Initialiserar instansvariabler.
        """
        
        super().__init__(model)  # bara model!
        self.unique_id = unique_id  # sätt unik ID själv
        self.status = status        # "S", "I", "R", "D"
        self.vaccinated = vaccinated
        self.days_infected = 0
        self.infector_id = None # Hur många personer den har smittat

    def move(self):
        """
        Syfte:
            Uppdaterar agentens position genom att flytta den till en slumpmässig
            intilliggande cell (kan även vara diagonalt).

        Input:
            Inga funktionella inputs (använder modellens grid och agentens aktuella position).

        Output:
            Flyttar agenten till en ny position i modellen.
        """
        
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True, # kan gå diagonalt 
            include_center=False # kan inte stanna kvar på samma ställe 
        )
        new_position = self.random.choice(possible_steps) # random steg 
        self.model.grid.move_agent(self, new_position) # uppdaterar position

    def try_infect(self, other):
        """
        Syfte:
            Försöker infektera en annan agent som befinner sig i samma cell.

        Input:
            other (SIRAgent): Den agent som eventuellt ska infekteras.

        Output:
            Ändrar 'other.status' till "I" vid lyckad infektion.
            Loggar infektionen i modellen.
            Uppdaterar SIRAgent.new_infected vid smittspridning.
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
        """
        Syfte:
            Returnerar det totala antalet nya infektioner under nuvarande tidssteg.

        Input:
            Inga.

        Output:
            (int): Antalet nya infektioner detta tidssteg.
        """
        return SIRAgent.new_infected

    def reset_new_infected(self):
        """
        Syfte:
            Nollställer räknaren för nya infektioner inför nästa tidssteg.

        Input:
            Inga.

        Output:
            Inga (uppdaterar klassvariabeln SIRAgent.new_infected).
        """
        
        SIRAgent.new_infected = 0
                

    def step(self):
        """
        Syfte:
            Definierar agentens beteende per tidssteg beroende på dess status.
            - Döda agenter gör inget.
            - Levande agenter rör sig.
            - Infekterade agenter försöker smitta andra.
            - Ökar antal dagar sjuka.
            - Hanterar dödsrisk och återhämtning.

        Input:
            Inga funktionella inputs (hämtar allt från modell och agentens status).

        Output:
            Uppdaterar agentens position, status och sjukdomsprogression.
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