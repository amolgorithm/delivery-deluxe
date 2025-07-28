# Delivery Deluxe

## Description

Delivery Deluxe is a 3D driving simulation game where players navigate a bustling city to pick up and deliver packages to houses within a time limit, strategically managing fuel resources and avoiding various penalties like speeding and collisions with NPCs. This application was developed for my final summative project in ICS3U.

## Features

* **Dynamic Day-Night Cycle:** Experience a realistic passage of time with changing lighting conditions that affect gameplay visibility.

* **Vehicle Customization:** Visit the garage to choose from a selection of distinct vehicle models, each with unique performance characteristics, and customize their color to your liking.

* **Physics-based Driving:** Enjoy a responsive and challenging driving experience with realistic vehicle physics for acceleration, braking, and handling.

* **NPC Traffic:** Navigate a city populated with walking non-player characters (NPCs) that react to the environment, adding to the urban feel. Collisions with these NPCs would result in fine penalties.

* **Delivery Missions:** Engage in a core gameplay loop of accepting new delivery requests, locating targets on the map, and delivering packages within a strict time limit.

* **Fuel Management & Refueling:** Keep an eye on your fuel gauge! Run out, and it's game over. Refuel at designated gas stations for a fee.

* **Speeding & Collision Fines:** Be a responsible driver! Speeding and hitting pedestrians will result in monetary fines, impacting your game progress.

* **Interactive Minimap:** Utilize a dynamic minimap in the top-right corner, which tracks your current position, delivery targets, and gas stations.

* **Autopilot Assistance:** For a fee, activate an autopilot feature that can guide your vehicle along the most time-efficient path to your delivery target.

* **Win/Loss Conditions:** The game features clear objectives for winning (successful deliveries) and losing (running out of resources or failing too often).

## How to Play / Objectives

**Core Objective:** Successfully complete five package deliveries to houses across the city while maximizing your money earned and your rating score (avg of all the customer ratings you receive - higher ratings for quicker deliveries).

**Gameplay Loop:**

1.  A new delivery target will appear on your minimap and dashboard.

2.  Navigate your vehicle to the pickup location (your current position).

3.  Drive to the delivery target shown on your dashboard and minimap before the timer runs out.

4.  Once at the delivery target, press the 'V' key to attempt to complete the delivery.

5.  Earn money for successful deliveries, which you can use to refuel your car or pay fines.

**Winning the Game:**

* Successfully complete **5 deliveries**.

**Losing the Game:**

* Running out of **fuel**.

* Accumulating **4 delivery failures**.

* Going **bankrupt** (money drops below $0).

## Controls

* **Arrow Keys (Up, Down, Left, Right):** Control vehicle acceleration, reverse, and steering.

* **Spacebar:** Apply manual brakes.

* **V:** Attempt to complete the current delivery when at the target location.

* **C:** Refuel your vehicle when positioned within a gas station area.

* **Z:** Zoom in on the minimap.

* **X:** Zoom out on the minimap.

* **Escape:** Quits the game from the start/end screens. During gameplay, it will interrupt and stop the autopilot assist.

* **Mouse Wheel (Scroll Up/Down):** Adjusts the main camera's zoom distance during gameplay.

## Garage Usage

The Garage is your hub for vehicle customization before starting a delivery.

1.  **Accessing the Garage:** From the main Start Screen, click "Start Game" to enter the garage.

2.  **Vehicle Selection:**

    * Use the **`<` (Left Arrow)** and **`>` (Right Arrow)** buttons positioned on either side of the car model to cycle through available vehicle models. Each model has different performance stats.

3.  **Color Customization:**

    * A **rainbow color grid** allows you to select the base hue for your vehicle.

    * A row of **saturation buttons** beneath the main color grid will dynamically update to show different shades and saturations of your currently selected hue. Click these to fine-tune your car's color.

4.  **Vehicle Specifications:** On the top-left of the screen, you'll see a panel displaying the selected vehicle's name, tier, and key performance indicators:

    * **Mass:** Affects handling and acceleration.

    * **Acceleration:** How quickly the car gains speed.

    * **Handling Coefficient:** Influences how well the car turns.

    * **Fuel Consumption:** How quickly your fuel depletes.
        These are visually represented by progress bars.

5.  **Start Delivery!** Once you've customized your ride, click the "Start Delivery!" button to begin your game.

## Autopilot Feature

The autopilot is a convenient but costly feature to assist you with deliveries.

* **Cost:** Activating the autopilot costs **$40**.

* **Activation:** Click the "Use Autopilot ($40)" button located on the dashboard during gameplay.

* **Functionality:** Once activated, your car will automatically drive itself along the most time-efficient path directly to your current delivery target.

* **Interruption:** You can interrupt the autopilot at any time by pressing the **`Escape`** key. The car will stop, and you will regain manual control.

* **Usage Limit:** The autopilot can only be used **once per game session**.

## Rules to be Aware Of

* **Time Management:** Every delivery has a strict time limit. Keep an eye on the "Time Left" display on your dashboard. If you fail to reach the delivery point before the timer hits zero, the delivery will be marked as a failure.

* **Fuel Economy:** Your vehicle constantly consumes fuel while driving. Monitor the fuel gauge on your dashboard. Running out of fuel results in an immediate game over. Visit gas stations (marked by a '+' on the minimap) and press 'C' to refuel.

* **Traffic Laws & Fines:**

    * **Speeding:** There are speed limits for different road types (displayed on your dashboard). If you continuously exceed the speed limit for 3 seconds, you will incur a **$5 fine**.

    * **Pedestrian Collisions:** Be cautious of pedestrians! Hitting an NPC will immediately result in a **$20 fine**. Repeated collisions will result in multiple fines.

* **Delivery Failures:** You are allowed up to 3 delivery failures. Your **4th failure** will result in an immediate game over.

* **Financial Stability:** Your money is crucial, remember this! If your total money drops below $0, you will go bankrupt, and the game will end as a loss. Manage your money wisely by completing deliveries properly and avoiding fines (so please don't run over the NPCs too much - protect pandas!).

## Installation

To run Delivery Deluxe, you need the following Python packages:

* **Panda3D:** The open-source game engine used to build the game.
    ```bash
    pip install panda3d=1.10.15
    ```
## Usage

Open a terminal and go to the project directory. Run the application:

```bash
python main.py
```

## Cheat Codes

* **Delivery Location Hint:** Your delivery destination will **always be a house**. Pay attention to the street number mentioned on your dashboard; a larger house number typically means the house is located further **east** along that street. This can help you narrow down your search and find the target faster.

* **Instant Refuel:** Drive to any gas station (marked with a '+' on the minimap) and press **`C`** to instantly refuel your vehicle to 100%. This is useful for quickly topping off your fuel without waiting or worrying about consumption.

* **Optimal Driving Strategy:** Don't be overly concerned about minor speeding or collision fines if the delivery reward greatly outweigh the cost. Getting to the destination faster can often result in a higher rating score, potentially earning you more money, which can more than reimburse for small fines. Prioritize efficiency over strict adherence to all rules if profit score and rating score is your main goal.

* **Autopilot Showcase:** Activate the "Use Autopilot" button on the dashboard to see the car navigate the shortest path to your delivery target automatically. This quickly demonstrates the pathfinding and automatic driving capabilities.

* **Garage Exploration:** Spend time in the garage to instantly preview all available vehicle models and customize their colors without starting a game. This allows for quick iteration and viewing of car options.

## Support

If you encounter any issues or require further assistance with Delivery Deluxe, please feel free to contact the developer:

**Amol Sriprasadh:**
 [amol.unique@gmail.com](mailto:amol.unique@gmail.com)

## Sources

**Reference Tracker:**
<https://docs.google.com/document/d/1qR3cMLyLMtx9jke_PAQFX4ISooGXWqAb76coX5gal-Q/edit?usp=sharing>
<br><br><br><br>
