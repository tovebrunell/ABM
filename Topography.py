import importlib
import Agenter
import Modell

importlib.reload(Agenter)
importlib.reload(Modell)

from Modell import SIRModel

from Agenter import SIRAgent
from mesa import Agent, Model
from mesa.space import MultiGrid
import random
import numpy as np

topography = np.zeros((70, 140), dtype=int)

