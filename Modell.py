import random

import numpy as np
import pandas as pd
from Agenter import SIRAgent
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

# Läs in kalkylarket som beskriver topografin och konvertera till numpy matrix
topography_df = pd.read_excel("Topografi karta.xlsx", header=None).transpose()
topography_matrix = topography_df.to_numpy()

#Funktion för att räkna ut Re
def compute_Re(modell):
    """
    Syfte: 
        Beräknar Re (effektivt reproduktionstal) baserat på andelen smittbara agenter gånger R0 värdet

    Input:
        modell (SIRModel): Modellinstansen.

    Output:
        float: Beräknat Re-värde.
    """
    
    return modell.R0 * modell.current_susceptible/modell.num_agents

#Funktion för att räkna ut R0
def compute_R0(modell):
    """
    Syfte:
        Beräknar R0 för specifikt tidssteg genom att ta kvoten av nya infektioner och 
        avklarade sjukdomsförlopp. 

    Input:
        modell (SIRModel): Modellinstansen.

    Output:
        float: Beräknat R0-värde. 0 om inga avklarade infektioner finns.
    """
    if modell.finished_infections:
        return modell.total_secondary_infections / modell.finished_infections
    else:
        return 0

#Modellen
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
        initial_infected (int): Antal initialt infekterade agenter. Default = 1
        vaccination_rate (float): Andel som är vaccinerade. Default = 0
        mortality_rate (float): Dödsrisk per infekterad agent per dag. Default = 0.01
        R0 (int): Uppskattat värde på reproduktionstalet R0. Default = 15

    Output:
        En instans av SIRModel.
    """
    
    def __init__(self, N, width, height, initial_infected=1, vaccination_rate=0.0, mortality_rate=0.01, R0=16):

        """
        Syfte:
            Skapar en ny SIR-modell med specificerat antal agenter, placerar dem på grid
            och initierar datastrukturer för att hålla koll på Re, infektioner och status.

        Input:
            N (int): Antalet agenter i modellen.
            width (int): Bredd på grid.
            height (int): Höjd på grid.
            initial_infected (int): Antal initialt infekterade agenter. Default = 1
            vaccination_rate (float): Andel som är vaccinerade. Default = 0
            mortality_rate (float): Dödsrisk per infekterad agent per dag. Default = 0.01
            R0 (int): Uppskattat värde på reproduktionstalet R0. Default = 15

        Output:
            Inga direkta return-värden. Initierar modellens starttillstånd.
        """
        
        super().__init__()
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.mortality_rate = mortality_rate
        self.R0 = R0

        # Agentlista (inte self.agents)
        self.agent_list = []

        self.new_infected = 0 # Antal nya infekterade under tidssteget

        self.new_infected_total = 0 # Summa av nya infekterade

        self.total_secondary_infections = 0 # Summa av antalet nya infektioner som skett från avklarade sjukdomsförlopp
        self.finished_infections = 0 # Antal avklarade sjukdomsförlopp

        #Datacollector funktion som samlar data för analys
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

        SIRAgent.reset_shared_variables(SIRAgent) # Återställer variabler som delas mellan modellen och agenterna.

        # Skapar N antal agenter, ger dem en hälsostatus, samt placerar agenterna slumpmässigt i vår grid.
        for i in range(N):

            if i < initial_infected: 
                status = "I"
            
            elif self.random.random() < vaccination_rate:
                status = "R"  # Vaccinerade och återhämtade betraktas båda som resistenta 

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
            - Räknar aktuellt antal agenter för varje hälsostatus
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
        self.new_infected = SIRAgent.get_new_infected(SIRAgent) 
        self.new_infected_total += self.new_infected 
        self.datacollector.collect(self) 
        SIRAgent.reset_new_infected(SIRAgent) # Återställer antalet nya infekterade för nästa tidssteg
        
        self.agents.shuffle_do("step") # Genomför tidssteget

        # Uppdaterar agenternas status enligt vad som skett i tidssteget 
        for agent in self.agent_list:
            agent.status = agent.next_state

    # Funktion för att räkna antal agenter med viss status
    def count_status(self, status):

        """
        Syfte:
            Räknar hur många agenter som har en viss status.

        Input:
            status (str): Den status som ska räknas.

        Output:
            int: Antal agenter med den givna statusen.
        """
        
        return sum(1 for a in self.agent_list if a.status == status)

    def status_update(self):
        
        """
        Syfte:
            Räknar antalet agenter med varje hälsostatus och uppdaterar datacollector värdena.

        Input:
            Inga externa input (hämtar data med count_status funktionen).

        Output:
            Inga direkta return värden. Uppdaterar current_susceptible, current_infected, 
            current_resistant, och current_dead.
        """
        
        self.current_susceptible = self.count_status("S")
        self.current_infected = self.count_status("I")
        self.current_resistant = self.count_status("R")
        self.current_dead = self.count_status("D")
