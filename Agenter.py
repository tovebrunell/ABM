import random

import numpy as np
import pandas as pd
from mesa import Agent, Model
from mesa.space import MultiGrid

# Läs in kalkylarket som beskriver topografin och konvertera till numpy matrix
topography_df = pd.read_excel("Topografi karta.xlsx", header=None).transpose()
topography_matrix = topography_df.to_numpy()

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
        
    Output:
        En instans av SIRAgent.
    """
    
    new_infected = 0
    
    def __init__(self, unique_id, model, status="S"):
        
       
        """
        Syfte:
            Initierar en SIR-agent med status, vaccinationstillstånd och trackar
            infektionstillstånd över tid.

        Input:
            unique_id (int): Agentens unika ID.
            model (Model): Modellen agenten tillhör.
            status (str): Startstatus ("S", "I", "R", "D").

        Output:
            Inga direkta return-värden. Initialiserar instansvariabler.
        """
        
        super().__init__(model)  # bara model!
        self.status = status        # "S", "I", "R", "D"
        self.days_infected = 0
        self.secondary_infections = 0 # Hur många personer den har smittat
        self.next_state = status # Används för att agenter inte ska kunna vara friska, bli infekterade, 
                                 # och infektera någon annan i ett och samma tidssteg

    #Funktion för när agenterna flyttar på sig i vår grid.
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

    # Hämtar aktuellt värde från topografin för din position 
    def get_topography(self):
        
        """
        Syfte:
            Tar agentens nuvarande position och hämtar befolkningstäthetsvärdet från topografi matrisen/kartan.

        Input:
            Inga funktionella inputs (använder modellens grid och agentens aktuella position).

        Output:
            float: värde befolkningstäthetsvärde för agentens position.
        """
        
        x, y = self.pos
        
        return topography_matrix[x, y]

    def try_infect(self, other):
        
        """
        Syfte:
            Försöker infektera en annan agent som befinner sig i samma eller angränsade cell. 

        Input:
            other (SIRAgent): Den agent som eventuellt ska infekteras.

        Output:
            Ändrar 'other.next_state' till "I" vid lyckad infektion.
            Loggar infektionen i modellen.
            Uppdaterar SIRAgent.new_infected vid smittspridning.
        """
        
        if other.status == "S" or other.status == "R": 
            topography_value = other.get_topography()

            if topography_value == 0:
                topography_coefficient = 0.1
            elif topography_value == 1:
                topography_coefficient = 1
            elif topography_value == 2:
                topography_coefficient = 10
            else:
                topography_coefficient = 0.01
                
            if other.status == "R": 
                # Resistenta har 3% risk att bli smittade
                infection_chance = 0.03 * 0.075 * topography_coefficient
            else:
                infection_chance = 1.0 * 0.075 * topography_coefficient
                
            if self.random.random() < infection_chance:
                other.next_state = "I"

                SIRAgent.new_infected += 1 # Lägger till en ny person som har smittats till den globala variabeln
                self.secondary_infections += 1 # Ökar antalet agenter som denna agent har smittat

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

    def reset_shared_variables(self):
        """
        Syfte:
            Nollställer de delade variablerna i klassen för varje ny körning.
        Input:
            Inga.

        Output:
            Inga.
        """
        SIRAgent.new_infected = 0
        
        SIRAgent.r0_new_infected = 0
        
        SIRAgent.r0_finished_infected = 0
        
    def finish_infection(self):
        """
        Syfte:
            Uppdaterar värdena i modellen som håller reda på antalet nya infektioner per 
            antalet avklarade infektioner och återställer räknare infför agentens nästa 
            eventuella sjukdomsförlopp. 
        Input:
            Inga.

        Output:
            Inga. 
        """
        self.model.total_secondary_infections += self.secondary_infections
        self.model.finished_infections += 1
        self.secondary_infections = 0
        self.days_infected = 0

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
            return  # döda varken rör på sig eller smittar

        self.move()
        
        if self.status == "I":

            # Tar positionerna för cellen agenten befinner sig och alla angränsande celler. 
            neighbor_positions = self.model.grid.get_neighborhood(self.pos,moore=True,include_center=True)
            
            for pos in neighbor_positions:
                agents_here = self.model.grid.get_cell_list_contents([pos])
            
                for other in agents_here:
                    if other == self: # Skippar sig själv
                        continue
            
                    else:
                        self.try_infect(other)
            

            # Öka dagar sjuk
            self.days_infected += 1

            # Dödsrisk
            if self.random.random() < self.model.mortality_rate:
                self.next_state = "D"
                self.finish_infection()
                return

            # Återhämtning efter 8 dagar
            elif self.days_infected >= 8:
                self.next_state = "R" # Vi antar att man inte kan bli sjuk 2 gånger! 
                self.finish_infection()
