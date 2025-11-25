from Agenter import SIRAgent
from mesa import Agent, Model
from mesa.space import MultiGrid
import random

class SIRModel(Model):
    def __init__(self, N, width, height, initial_infected=1, vaccination_rate=0.0, mortality_rate=0.01):
        super().__init__()
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.mortality_rate = mortality_rate

        # Agentlista (inte self.agents)
        self.agent_list = []

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
        self.random.shuffle(self.agent_list)
        for agent in self.agent_list:
            agent.step()

    # Funktion för att räkna antal agenter med viss status
    def count_status(self, status):
        return sum(1 for a in self.agent_list if a.status == status)
