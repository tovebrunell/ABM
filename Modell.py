from Agenter import SIRAgent
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random

def compute_Re(self, current_infected_count):
        return SIRAgent.get_new_infected(SIRAgent) / current_infected_count if current_infected_count else 0

class SIRModel(Model):
    def __init__(self, N, width, height, initial_infected=1, vaccination_rate=0.0, mortality_rate=0.01):
        super().__init__()
        self.infection_log = []  # lista med alla infektioner
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.mortality_rate = mortality_rate

        # Agentlista (inte self.agents)
        self.agent_list = []
        
        # Lista för att spara Re över tid 
        self.Re_history = []

        self.new_infections = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Re": compute_Re  # Funktion för att räkna ut Re (definierad längre ner)
            },
            agent_reporters={
                "Agent status": "status",
                "Agent position": "pos",
            },  # agent egenskaper
        )
        self.current_day = 0

        for i in range(N):
            vaccinated = self.random.random() < vaccination_rate
            if i < initial_infected:
                status = "I"
            elif vaccinated:
                status = "R"  # Vaccinerade räknas som immun
            else:
                status = "S"

            agent = SIRAgent(i, self, status=status, vaccinated=vaccinated)
            self.agent_list.append(agent)

            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        #self.datacollector.collect(self)   # Detta är en data collector som han använder i föreläsningsexmplet och är rätt bra men är inte implementerad ännu.

        current_infected_count = self.count_status("I")
        
        self.agents.shuffle_do("step")

        secondary = {}
        for event in self.infection_log:
            if event["day"] == self.current_day: 
                
                inf = event["infector_id"]
                
                if inf is not None:
                    secondary[inf] = secondary.get(inf, 0) + 1

        Re = compute_Re(self, current_infected_count)
        
        self.Re_history.append(Re)
        SIRAgent.reset_new_infected(SIRAgent)

        self.current_day += 1 

    # Funktion för att räkna antal agenter med viss status
    def count_status(self, status):
        return sum(1 for a in self.agent_list if a.status == status)
        
    # Funktion för att logga infection
    def log_infection(self, agent):
        self.infection_log.append({
            "case_id": agent.unique_id, # vem har blivit smittad
            "infector_id": agent.infector_id, # vem har smittat
            "day": len(self.infection_log)  # Vilken dag? 
            "day": self.current_day  # Vilken dag? 


        })
