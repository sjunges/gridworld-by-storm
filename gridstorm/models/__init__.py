import os
from gridstorm.annotations import ProgramAnnotation, Direction

class Model:
    def __init__(self, path, annotations, properties, constants="", ego_icon=None):
        self._path = path
        self._anonotations = annotations
        self._properties = properties
        self._ego_icon = ego_icon
        self._constants = constants

    @property
    def path(self):
        return self._path

    @property
    def annotations(self):
        return self._anonotations

    @property
    def properties(self):
        return self._properties

    @property
    def ego_icon(self):
        return self._ego_icon

    @property
    def constants(self):
        return self._constants

class Icon:
    def __init__(self, path, zoom=0.2):
        self.path = path
        self._zoom = zoom

    @property
    def zoom(self):
        return self._zoom


def _example_path(extension):
    return os.path.join(os.path.dirname(__file__),'files',extension)


def _icon_path(suffix):
    return os.path.join(os.path.dirname(__file__), 'icons', suffix)

_grid_obstacle_dict = dict({'ego-xvar-module' : 'robot',
                      'ego-xvar-name' : 'ax',
                      'ego-yvar-module' : 'robot',
                      'ego-yvar-name': 'ay',
                      'xmax-constant': 'axMAX',
                      'ymax-constant': 'ayMAX',
                      'target-label': 'goal',
                      'traps-label': 'traps'
                      })
def obstacle(N, full_observable = False):
    if full_observable:
        return Model(_example_path("obstacle_full_observable.nm"), ProgramAnnotation(_grid_obstacle_dict),
                     ["Pmax=? [ \"notbad\" U \"goal\"]"], constants=f"N={N}")
    return Model(_example_path("obstacle.nm"), ProgramAnnotation(_grid_obstacle_dict),
                 ["Pmax=? [ \"notbad\" U \"goal\"]"], constants=f"N={N}")

_drone_dict = dict({'ego-xvar-module' : 'drone',
                      'ego-xvar-name' : 'dx',
                      'ego-yvar-module' : 'drone',
                      'ego-yvar-name': 'dy',
                      'adv-xvar-module': 'agent',
                        'adv-xvar-name': 'ax',
                        'adv-yvar-module': 'agent',
                        'adv-yvar-name': 'ay',
                        'xmax-constant': 'xMAX',
                      'ymax-constant': 'yMAX',
                      'target-label': 'goal',
                       'ego-radius-constant' : "RADIUS",
                       'scan-action': 'scan',
                        'adv-area': ['a'],
                      'traps-label': None
                      })

def evade(N,RADIUS):
    return Model(_example_path("evade.nm"), ProgramAnnotation(_drone_dict),
                 ["Pmax=? [\"notbad\" U \"goal\"]"], constants=f"N={N},RADIUS={RADIUS}")

_intercept_dict = dict({'ego-xvar-module' : 'drone',
                      'ego-xvar-name' : 'dx',
                      'ego-yvar-module' : 'drone',
                      'ego-yvar-name': 'dy',
                      'adv-xvar-module': 'agent',
                        'adv-xvar-name': 'ax',
                        'adv-yvar-module': 'agent',
                        'adv-yvar-name': 'ay',
                        'xmax-constant': 'dxMAX',
                      'ymax-constant': 'dyMAX',
                      'traps-label': None,
                        'ego-radius-constant': "RADIUS",
                        'camera': ['CAMERA'],
                        'adv-goals-label': 'exits'
                      })
def intercept(N,RADIUS):
    return Model(_example_path("intercept.nm"), ProgramAnnotation(_intercept_dict),
                 ["Pmax=? [\"notbad\" U \"goal\"]"], constants=f"N={N},RADIUS={RADIUS}")


_surveillance_dict = dict({'ego-xvar-module' : 'drone',
                      'ego-xvar-name' : 'dx',
                      'ego-yvar-module' : 'drone',
                      'ego-yvar-name': 'dy',
                      'adv-xvar-module': ['agent','agent2'],
                       'adv-xvar-name': ['ax','ax2'],
                       'adv-yvar-module': ['agent','agent2'],
                        'adv-yvar-name': ['ay','ay2'],
                       'adv-dirvar-module': ['agent', 'agent2'],
                           'adv-dirvar-name': ['dir', 'dir2'],
                           'xmax-constant': 'xMAX',
                      'ymax-constant': 'yMAX',
                      'target-label': 'goal',
                      'traps-label': None,
                      'adv-dirvalue-mapping': {1: Direction.WEST, 0: Direction.EAST},
                       'adv-radius-constant' : "ARADIUS",
                       'ego-radius-constant' : "RADIUS"
                      })
def surveillance(N,RADIUS=2):
    return Model(_example_path("avoid.nm"), ProgramAnnotation(_surveillance_dict), ["Pmax=? [\"notbad\" U \"goal\"]"], constants=f"N={N},RADIUS={RADIUS}")

_grid_refuel = dict({'ego-xvar-module' : 'rover',
                      'ego-xvar-name' : 'ax',
                      'ego-yvar-module' : 'rover',
                      'ego-yvar-name': 'ay',
                      'xmax-constant': 'axMAX',
                      'ymax-constant': 'ayMAX',
                      'target-label': 'goal',
                      'traps-label': 'traps',
                      'landmarks': 'stationvisit',
                      'resource-module': 'tank',
                      'resource-variable': 'fuel',
                      'resource-name': 'fuel',
                       'resource-maximum-constant': 'fuelCAP'
                      })

def refuel(N, ENERGY):
    return Model(_example_path("refuel.nm"), ProgramAnnotation(_grid_refuel), ["Pmax=? [\"notbad\" U \"goal\"]"], constants=f"N={N},ENERGY={ENERGY}")

_grid_rocks = dict({'ego-xvar-module' : 'robot',
                      'ego-xvar-name' : 'x',
                      'ego-yvar-module' : 'robot',
                      'ego-yvar-name': 'y',
                      'xmax-constant': 'xMAX',
                      'ymax-constant': 'yMAX',
                      'target-label': 'goal',
                      'traps-label' : None,
                      'interactive-landmarks-x': ['r1x', 'r2x'],
                      'interactive-landmarks-y': ['r1y', 'r2y'],
                      'il-statusvar-module': ['rock1', 'rock2'],
                      'il-statusvar-name': ['r1qual', 'r2qual'],
                      'il-clearancevar-module': ['rock1', 'rock2'],
                      'il-clearancevar-name': ['r1taken', 'r2taken'],
                       'goal-action' : True
                    })

def rocks(N, K=2):
    K = int(K)
    if K == 2:
        return Model(_example_path("rocks2.nm"), ProgramAnnotation(_grid_rocks), ["Pmax=? [\"notbad\" U \"goal\"]"], constants=f"N={N}")
    else:
        raise RuntimeError("Rocks is only available with 2 or 3 rocks")