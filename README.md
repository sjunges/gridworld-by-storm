# Gridworld-By-Storm

is a small project that investigates how POMDP analysis results in storm can be visualised.
For that, the project currently contains 
- a series of gridworlds, and 
- a renderer to render traces in these gridworlds.
- a demo.py demonstrating how to generate and render traces

For more advanced usage, we can refer to the [rlshield](https://github.com/sjunges/shield-in-action) project that builds on top of this project. 

# Installation

- Ensure FFMPeg is available on your system.
- Ensure Stormpy 1.7.0 is available on your system.

# Gridworlds

## Included benchmarks

#### Evade
In this example, our robot needs to arrive at a destination (bottom right) without being intercepted by a faster agent. The top row is only accessible by the robot, which also has a limited view radius $R$, but can instead of moving scan the full grid to disclose the current position of the agent.

#### Avoid
A variant of Evade: our robot needs to reach a target area (bottom of the grid). 
It needs to remain undetected (keep a distance) by two moving agents, but may exploit that the agents  patrol certain preset routes. Their speed is uncertain, so their position along the patrolled area is unknown unless within the view radius. 

#### Intercept
The 'inverse' problem to Evade. Our robot moves in 8 directions, has a limited view radius $R$, and via cameras observes  a west-to-east corridor in the center of the grid. Our robot wants to meet an agent moving in four directions, before that agent leaves the area via two exits at the west corners. Cameras observe

#### Obstacle
Obstacle is a grid with known static obstacles where the robot needs to find the exit. Its initial state and movement are uncertain, and it only observes whether the current position is a trap or exit. 

#### Rocks
Rocks adapts obstacle: Rather than obstacles, the grid contains 2 rocks, which are either valuable or dangerous to collect. To find out with certainty, the rock has to be sampled from some adjacent field. The goal is to collect at least one valuable rock (if a valuable rock is in the grid) and bring it to the drop-off zone. No dangerous rocks should be collected.

#### Refuel
Our rover needs to travel from A (upper-left corner) to B (lower-right corner), while avoiding an obstacle on the diagonal between A and B. 
The rover may detect the edges of the grid, but does not know its exact position. 
The rover can move in any of the 4 cardinal directions, but the distance travelled is uncertain. Every action costs energy. Therefore, the rover must recharge to E energy at recharging stations (in this instance also at the diagonal between A and B).

## Adding your own
TBD
