<div align="center">
    <h1>Multi-Agent Autonomous Waste Collection System</h1>
</div>

<p align="center" width="100%">
    <img src="./Multi-Agent-Autonomous-Waste-Collection-System/Assets/GarbageMan.png" width="55%" height="55%" alt="Multi-Agent Autonomous Waste Collection System"/>
</p>

<div align="center">
    <a>
        <img src="https://img.shields.io/badge/Made%20with-Python-6A9C89?style=for-the-badge&logo=Python&logoColor=6A9C89">
    </a>
    <a>
        <img src="https://img.shields.io/badge/Made%20with-SPADE-6A9C89?style=for-the-badge&logo=robotframework&logoColor=6A9C89">
    </a>
</div>

<br/>

<div align="center">
    <a href="https://github.com/EstevesX10/Multi-Agent-Autonomous-Waste-Collection-System/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/EstevesX10/Multi-Agent-Autonomous-Waste-Collection-System?style=flat&logo=gitbook&logoColor=6A9C89&label=License&color=6A9C89">
    </a>
    <a href="#">
        <img src="https://img.shields.io/github/repo-size/EstevesX10/Multi-Agent-Autonomous-Waste-Collection-System?style=flat&logo=googlecloudstorage&logoColor=6A9C89&logoSize=auto&label=Repository%20Size&color=6A9C89">
    </a>
    <a href="#">
        <img src="https://img.shields.io/github/stars/EstevesX10/Multi-Agent-Autonomous-Waste-Collection-System?style=flat&logo=adafruit&logoColor=6A9C89&logoSize=auto&label=Stars&color=6A9C89">
    </a>
    <a href="https://github.com/EstevesX10/Multi-Agent-Autonomous-Waste-Collection-System/blob/main/SETUP.md">
        <img src="https://img.shields.io/badge/Setup-SETUP.md-white?style=flat&logo=springboot&logoColor=6A9C89&logoSize=auto&color=6A9C89"> 
    </a>
</div>

## Project Overview

### Problem Scenario

In large **urban areas**, managing **waste collection** efficiently is a challenge, especially with varying levels of waste production and **changing road conditions** (e.g., traffic, roadblocks). Instead of a centrally controlled system, autonomous garbage trucks are deployed to handle waste collection, where each truck operates as an **independent agent**. These agents must work together to **optimize routes**, avoid redundant collections, and **manage limited resources** such as fuel or battery levels.

### Objective

Design and implement a **decentralized waste collection system** using Multi-Agent Systems (MAS) with **SPADE**. The system will **simulate autonomous garbage trucks** (agents) that collaborate to **efficiently collect waste from various locations** within a city, responding dynamically to changes in waste levels and traffic conditions.

### Key Features

1. `Truck Agents`: Each **truck** is represented by an agent responsible for **collecting waste** from assigned areas. These agents can **detect the fill levels of nearby waste bins** and **decide whether to collect** based on factors such as current waste capacity, fuel or battery level, and proximity to the bin.

2. `Bin Agents`: **Waste bins** are also represented by agents that **regularly report their fill levels** to nearby truck agents. When the fill level reaches a defined threshold, they **trigger a collection request to the closest truck agents**.

3. `Decentralized Decision-Making`: The system is fully **decentralized**, meaning each truck agent makes **independent decisions** about when to collect waste, where to go next, and how to optimize its route. **No central controller is required**. Agents **communicate with each other** to prevent overlapping collection areas and **ensure full city coverage**.

4. `Dynamic Environment`: The environment includes **dynamic factors** such as changing traffic conditions, roadblocks, and fluctuating waste production. Truck agents must **adjust their routes** in real-time based on these factors to ensure **efficient operation**.

5. `Task Allocation and Collaboration`: The system uses a **negotiation or task allocation protocol** (e.g., **Contract Net Protocol**) that allows truck agents to **share responsibilities and delegate tasks** to nearby agents if they are overloaded. This ensures **efficient coverage** of all waste bins.

6. `Resource Management`: Each truck has **limited resources**, such as fuel/battery life and waste capacity. Truck agents need to plan their routes to **minimize fuel consumption while maximizing the amount of waste collected per trip**. When necessary, trucks return to a central depot to unload or recharge.

7. `Optimization Metrics`: The system tracks several **key performance metrics** to measure efficiency:

   - **Total waste collected**

   - **Average collection time per bin**

   - **Total fuel or battery consumption**

   - **Distance traveled by each truck agent**

   - **Efficiency of collaboration and task allocation**

8. `Fault Tolerance`: The system is built to **handle agent failures**, such as trucks going offline or breaking down. When this occurs, the remaining agents automatically **redistribute tasks** to ensure waste collection continues without interruption.

## Environment Setup

If you plan to test this project yourself, make sure to review the **Environment** details by checking the [SETUP.md](https://github.com/EstevesX10/Multi-Agent-Autonomous-Waste-Collection-System/blob/main/SETUP.md) file for more information.

## Project Results

<!-- Developed Layouts  -->

### Environment Layouts

<table width="100%">
    <thead align="center">
        <th colspan="4">
            <div align="center">Developed Layouts</div>
        </th>
    </thead>
    <tbody>
        <tr>
            <td></td>
            <td>
                <div align="center">
                    Layout-1
                </div>
            </td>
            <td>
                <div align="center">
                    Layout-2
                </div>
            </td>
            <td>
                <div align="center">
                    Layout-3
                </div>
            </td>
        </tr>
        <tr>
            <td width="10%">
                <p align="center" width="100%">
                    GUI
                </p>
            </td>
            <td width="30%">
                <p align="center">
                    <img src="./Multi-Agent-Autonomous-Waste-Collection-System/Assets/Layout1-GUI.png"/>
                </p>
            </td>
            <td width="30%">
                <p align="center">
                    <img src="./Multi-Agent-Autonomous-Waste-Collection-System/Assets/Layout2-GUI.png"/>
                </p>
            </td>
            <td width="30%">
                <p align="center">
                    <img src="./Multi-Agent-Autonomous-Waste-Collection-System/Assets/Layout3-GUI.png"/>
                </p>
            </td>
        </tr>
    </tbody>
</table>

<!-- Project Results -->

### **Project Results [Layout-2]**

| **Trash Generated** | **Baseline** | **Increased Number of Trucks** | **Increased Number of Bins** |
| :-----------------: | :----------: | :----------------------------: | :--------------------------: |
|         386         |     386      |              386               |             842              |
|         475         |     475      |              572               |             856              |
|         287         |     287      |               92               |             724              |
|          0          |      0       |               0                |              11              |
|         267         |     267      |               66               |             321              |
|        34.00        |    34.00     |             12.28              |             46.8             |
|        21.22        |    21.22     |             20.14              |            24.98             |

## Authorship

- **Authors** &#8594; [Gonçalo Esteves](https://github.com/EstevesX10), [Nuno Gomes](https://github.com/NightF0x26) and [Pedro Afonseca](https://github.com/PsuperX)
- **Course** &#8594; Introduction to Intelligent Autonomous Systems [[CC3042](https://sigarra.up.pt/fcup/en/ucurr_geral.ficha_uc_view?pv_ocorrencia_id=546531)]
- **University** &#8594; Faculty of Sciences, University of Porto

<div align="right">
<sub>

<!-- <sup></sup> -->

`README.md by Gonçalo Esteves`
</sub>

</div>
