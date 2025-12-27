from Agenter import SIRAgent
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import pandas as pd
import numpy as np
import random

# Läs in kalkylarket som beskriver topografin och konvertera till numpy matrix
topography_df = pd.read_excel("Topografi karta.xlsx", header=None).transpose()
topography_matrix = topography_df.to_numpy()

def compute_Re(self):
        return self.R0 * self.current_susceptible/self.num_agents

def compute_R0(self):
        
        if self.finished_infections:
            return self.total_secondary_infections / self.finished_infections
        else:
            return 0
        
        #return self.r0_new_infected / self.r0_finished_infected if self.r0_finished_infected else 0

        """
        Syfte:
            Beräknar momentant Re (effektivt reproduktionstal) baserat på antal nya
            infektioner detta tidssteg och nuvarande antal infekterade.

        Input:
            self (SIRModel): Modellinstansen.
            current_infected_count (int): Antal infekterade vid aktuellt tidssteg.

        Output:
            float: Beräknat Re-värde. 0 om inga infekterade finns.
        """

class SIRModel(Model):

    """
    Syfte:
        Implementerar en agentbaserad SIR-modell för smittspridning av mässlingen.
        Hanterar skapandet av agenter, rutnätet, uppdatering av modellen per tidssteg,
        loggning av infektioner och beräkning av epidemiologiska mått som Re.

    Input:
        N (int): Antalet agenter i modellen.
        width (int): Bredd på grid.
        height (int): Höjd på grid.
        initial_infected (int): Antal initialt infekterade agenter.
        vaccination_rate (float): Andel som är vaccinerade.
        mortality_rate (float): Dödsrisk per infekterad agent per dag.

    Output:
        En instans av SIRModel.
    """
    
    def __init__(self, N, width, height, initial_infected=1, vaccination_rate=0.0, mortality_rate=0.01, R0=15):

        """
        Syfte:
            Skapar en ny SIR-modell med specificerat antal agenter, placerar dem på grid
            och initierar data­strukturer för att hålla koll på Re, infektioner och status.

        Input:
            N (int): Antalet agenter.
            width (int): Grid-bredd.
            height (int): Grid-höjd.
            initial_infected (int): Antal som börjar som infekterade.
            vaccination_rate (float): Andel agenter som vaccineras.
            mortality_rate (float): Sannolikhet att en infekterad agent dör per dag.

        Output:
            Inga direkta return-värden. Sätter upp modellens starttillstånd.
        """
        
        super().__init__()
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.mortality_rate = mortality_rate
        self.R0 = R0

        # Agentlista (inte self.agents)
        self.agent_list = []
        
        # Lista för att spara Re över tid 
        self.Re_history = []

        self.new_infected = 0

        self.new_infected_total = 0

        self.total_secondary_infections = 0
        self.finished_infections = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Re": compute_Re,  # Funktion för att räkna ut Re (definierad ovanför klassen)
                "R0": compute_R0,  # Funktion för att räkna ut R0 (definierad ovanför klassen)
                "New Infected": "new_infected",
                "Susceptible": "current_susceptible",
                "Infected": "current_infected",
                "Resistant": "current_resistant",
                "Dead": "current_dead",
                "Total New Infected": "new_infected_total"
            },
            agent_reporters={
                "Agent status": "status",
                "Agent position": "pos",
            },  # agent egenskaper
        )
        self.current_day = 0

        SIRAgent.reset_shared_variables(SIRAgent)

        for i in range(N):

            if i < initial_infected: 
                status = "I"
            
            elif self.random.random() < vaccination_rate:
                status = "R"  # Vaccinerade räknas som immun

            else:
                status = "S"

            agent = SIRAgent(i, self, status=status)
            self.agent_list.append(agent)

            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

        self.current_susceptible = sum(1 for a in self.agent_list if a.status == "S")
        self.current_infected = sum(1 for a in self.agent_list if a.status == "I")
        self.current_resistant = sum(1 for a in self.agent_list if a.status == "R")
        self.current_dead = 0
        

    def step(self):

        """
        Syfte:
            Kör ett tidssteg av modellen:
            - Räknar aktuellt antal infekterade
            - Kör alla agenters step-funktion
            - Loggar sekundärfall för smittkedjor
            - Beräknar och sparar Re
            - Nollställer räknare för nya infektioner
            - Uppdaterar aktuell dag

        Input:
            Inga externa input (hämtar data från agent_list, grid och logs).

        Output:
            Inga direkta return-värden. Uppdaterar modellens tillstånd.
        """
        
        self.status_update()
        self.current_susceptible = self.count_status("S")
        self.current_infected = self.count_status("I")
        self.current_resistant = self.count_status("R")
        self.current_dead = self.count_status("D")
        self.new_infected = SIRAgent.get_new_infected(SIRAgent)
        self.new_infected_total += self.new_infected
        self.r0_new_infected, self.r0_finished_infected = SIRAgent.get_r0_new_infected(SIRAgent)
        self.datacollector.collect(self)
        SIRAgent.reset_new_infected(SIRAgent)

        
        self.agents.shuffle_do("step")

        for agent in self.agent_list:
            agent.status = agent.next_state

    # Funktion för att räkna antal agenter med viss status
    def count_status(self, status):

        """
        Syfte:
            Räknar hur många agenter som har en viss status
            (t.ex. 'S', 'I', 'R', 'D').

        Input:
            status (str): Den status som ska räknas.

        Output:
            int: Antal agenter med den givna statusen.
        """
        
        return sum(1 for a in self.agent_list if a.status == status)

    def status_update(self):
        self.current_susceptible = self.count_status("S")
        self.current_infected = self.count_status("I")
        self.current_resistant = self.count_status("R")
        self.current_dead = self.count_status("D")
