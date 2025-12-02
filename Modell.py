from Agenter import SIRAgent
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random

def compute_Re(self, current_infected_count):

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
    
        return SIRAgent.get_new_infected(SIRAgent) / current_infected_count if current_infected_count else 0

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
    
    def __init__(self, N, width, height, initial_infected=1, vaccination_rate=0.0, mortality_rate=0.01):

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
        
    # Funktion för att logga infection
    def log_infection(self, agent):
        
        """
        Syfte:
            Loggar en infektion till modellens infektion_log, inklusive
            vem som blev smittad, vem som smittade och vilken dag det skedde.

        Input:
            agent (SIRAgent): Agenten som precis blivit infekterad.

        Output:
            Inga direkta return-värden. Lägger till ett nytt event i infection_log.
        """
        
        self.infection_log.append({
            "case_id": agent.unique_id, # vem har blivit smittad
            "infector_id": agent.infector_id, # vem har smittat
            "day": len(self.infection_log),  # Vilken dag? 
            "day": self.current_day  # Vilken dag? 


        })
