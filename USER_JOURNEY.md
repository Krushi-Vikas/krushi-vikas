# 📊 Krushi Vikas - Multi-Tier Project Hierarchy & Complete Lateral Isolation

![Multi-Tier Project Hierarchy and Complete Lateral Isolation at All Levels](docs/project_hierarchical_update_flowchart.jpg)

This document details the **Role Hierarchy**, **Complete 3-Level Lateral Isolation**, **Vertical Downward Update Authority**, and **Step-by-Step User Journeys** with respect to **Projects**, **Activities**, and **Tasks** in the Krushi Vikas system.

---

## 🏛️ 1. Role Hierarchy (5-Tier Rank)

```mermaid
graph TD
    CEO["👑 1. CEO<br/><i>(Executive Authority & Org-Wide Super Access)</i>"]
    PD["🌟 2. Project Director<br/><i>(Strategic Direction & Cross-Portfolio Access)</i>"]
    PC["📋 3. Project Coordinator<br/><i>(Project Creator & Project Level Owner)</i>"]
    PM["⚙️ 4. Project Manager<br/><i>(Activity Level Owner & Delivery Lead)</i>"]
    FO["🌱 5. Field Officer<br/><i>(Task Level Owner & Survey Specialist)</i>"]

    CEO --> PD --> PC --> PM --> FO

    classDef exec fill:#1e1b4b,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef dir fill:#172554,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef coord fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef mgr fill:#451a03,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef fo fill:#083344,stroke:#06b6d4,stroke-width:2px,color:#fff;

    class CEO exec;
    class PD dir;
    class PC coord;
    class PM mgr;
    class FO fo;
```

---

## 🔒 2. Multi-Tier Hierarchy & 3-Level Lateral Isolation

```mermaid
flowchart TD
    subgraph GLOBAL["👑 Executive Tier"]
        EXEC["👑 CEO & 🌟 Project Director<br/><i>(Master Access Keys Across All Projects in Organization)</i>"]
    end

    subgraph TREE_A["📁 Tree A (Project A)"]
        PC1["📋 Project Coordinator 1 (PC1)<br/><b>Owner: Project A</b>"]
        PM1["⚙️ Project Manager 1 (PM1)<br/><b>Owner: Activity A1</b>"]
        FO1["🌱 Field Officer 1 (FO1)<br/><b>Owner: Task A1</b>"]
        
        PC1 -->|"⬇️ Vertical Authority: PC1 can edit Activity A1"| PM1
        PM1 -->|"⬇️ Vertical Authority: PM1 can edit Task A1"| FO1
        PC1 -->|"⬇️ Vertical Authority: PC1 can edit Task A1"| FO1
    end

    subgraph TREE_B["📁 Tree B (Project B)"]
        PC2["📋 Project Coordinator 2 (PC2)<br/><b>Owner: Project B</b>"]
        PM2["⚙️ Project Manager 2 (PM2)<br/><b>Owner: Activity B1</b>"]
        FO2["🌱 Field Officer 2 (FO2)<br/><b>Owner: Task B1</b>"]
        
        PC2 -->|"⬇️ Vertical Authority: PC2 can edit Activity B1"| PM2
        PM2 -->|"⬇️ Vertical Authority: PM2 can edit Task B1"| FO2
        PC2 -->|"⬇️ Vertical Authority: PC2 can edit Task B1"| FO2
    end

    %% Global Super Access
    EXEC ==>|"🔑 Master Key: Edit ANY Record"| TREE_A
    EXEC ==>|"🔑 Master Key: Edit ANY Record"| TREE_B

    %% Complete Lateral Isolation at All 3 Levels
    PC1 <-.->|"⛔ LEVEL 1 (PROJECT ISOLATION): PC1 cannot edit Project B, PC2 cannot edit Project A"| PC2
    PM1 <-.->|"⛔ LEVEL 2 (ACTIVITY ISOLATION): PM1 cannot edit Activity B1, PM2 cannot edit Activity A1"| PM2
    FO1 <-.->|"⛔ LEVEL 3 (TASK ISOLATION): FO1 cannot edit Task B1, FO2 cannot edit Task A1"| FO2
```

---

## 📋 3. Update Rights Summary Matrix

| Role | Edit Project | Edit Activity | Edit Task | Edit Survey |
| :--- | :--- | :--- | :--- | :--- |
| **👑 1. CEO** | ✅ **ANY** Project across organization | ✅ **ANY** Activity across organization | ✅ **ANY** Task across organization | ✅ **ANY** Survey |
| **🌟 2. Project Director** | ✅ **ANY** Project across organization | ✅ **ANY** Activity across organization | ✅ **ANY** Task across organization | ✅ **ANY** Survey |
| **📋 3. Project Coordinator** | ✅ **ONLY** projects owned by him<br>⛔ *Peer Coordinators blocked* | ✅ **ANY** Activity in his project<br>⛔ *Activities in other projects blocked* | ✅ **ANY** Task in his project<br>⛔ *Tasks in other projects blocked* | ✅ Surveys in his project |
| **⚙️ 4. Project Manager** | ❌ Read-Only on Projects | ✅ **ONLY** activities assigned to him<br>⛔ *Peer Managers blocked* | ✅ **ANY** Task in his assigned activity<br>⛔ *Tasks in other activities blocked* | ✅ Surveys in his activity |
| **🌱 5. Field Officer** | ❌ Read-Only on Projects | ❌ Read-Only on Activities | ✅ **ONLY** tasks assigned to him<br>⛔ *Peer Officers blocked* | ✅ **ONLY** surveys filed by him |

---

## 🗺️ 4. Multi-Tier End-to-End User Journey

```mermaid
sequenceDiagram
    autonumber
    actor CEO as 👑 CEO
    actor PD as 🌟 Project Director
    actor PC1 as 📋 Project Coordinator (PC1)
    actor PC2 as 📋 Other Coordinator (PC2)
    actor PM1 as ⚙️ Project Manager (PM1)
    actor PM2 as ⚙️ Other Manager (PM2)
    actor FO1 as 🌱 Field Officer (FO1)
    actor FO2 as 🌱 Other Officer (FO2)
    participant Sys as 💻 Krushi Vikas Core

    Note over PC1,Sys: 1. Level 1 (Project Isolation & Ownership)
    PC1->>Sys: Create Project A (Assigns self as PC1, PM1 as Activity Owner)
    Sys-->>PC1: ✅ Project A Created & Assigned to PC1
    PC2->>Sys: Attempt to edit Project A
    Sys-->>PC2: ❌ Blocked: Level 1 Isolation (PC2 does not own Project A)

    Note over PM1,Sys: 2. Level 2 (Activity Isolation & Downward Authority)
    PM1->>Sys: Edit Activity A1 (Timeline, Budget, Scope)
    Sys-->>PM1: ✅ Saved: PM1 is the assigned owner of Activity A1
    PM2->>Sys: Attempt to edit Activity A1
    Sys-->>PM2: ❌ Blocked: Level 2 Isolation (PM2 does not own Activity A1)
    PC1->>Sys: PC1 edits Activity A1 (under Project A)
    Sys-->>PC1: ✅ Saved: Vertical Downward Authority (PC1 owns Project A)

    Note over FO1,Sys: 3. Level 3 (Task Isolation & Downward Authority)
    FO1->>Sys: Update progress & submit outputs on Task A1
    Sys-->>FO1: ✅ Saved: FO1 is the assigned owner of Task A1
    FO2->>Sys: Attempt to edit Task A1
    Sys-->>FO2: ❌ Blocked: Level 3 Isolation (FO2 does not own Task A1)
    PM1->>Sys: PM1 edits Task A1 (under Activity A1)
    Sys-->>PM1: ✅ Saved: Vertical Downward Authority (PM1 owns Activity A1)
    PC1->>Sys: PC1 edits Task A1 (under Project A)
    Sys-->>PC1: ✅ Saved: Vertical Downward Authority (PC1 owns Project A)

    Note over PD,CEO: 4. Executive Super-Access Tier
    PD->>Sys: Project Director edits Project A, Activity A1, or Task A1
    Sys-->>PD: ✅ Saved: Strategic Super-Access across all trees
    CEO->>Sys: CEO edits Project A, Activity A1, or Task A1
    Sys-->>CEO: ✅ Saved: Executive Super-Access across all trees
```

---

## 👤 5. Detailed Breakdown by Role

### 👑 1. CEO (Executive Tier)
- **Scope**: Organization-wide unrestricted access.
- **Update Capabilities**: Can create, view, modify, approve, or delete **any** Project, Activity, Task, or Survey without needing to be in that specific project's ownership chain.

### 🌟 2. Project Director (Strategic Governance Tier)
- **Scope**: Cross-portfolio strategic leadership.
- **Update Capabilities**: Can create, modify, and manage **any** Project, Activity, Task, or Survey across all thematic areas and coordinators.

### 📋 3. Project Coordinator (Project Owner Tier)
- **Scope**: Project-level ownership.
- **Update Capabilities**:
  - **Project**: Can edit **only** projects assigned to them (`project_coordinator == session.user`). Peer coordinators (`PC2`) are strictly blocked (**Level 1 Isolation**).
  - **Activity**: Can edit **any** Activity belonging to their owned project (`Activity A1`).
  - **Task**: Can edit **any** Task belonging to their owned project (`Task A1`).

### ⚙️ 4. Project Manager (Activity Delivery Tier)
- **Scope**: Activity-level ownership and delivery.
- **Update Capabilities**:
  - **Project**: Read-only access.
  - **Activity**: Can edit **only** activities assigned to them (`assignee == session.user`). Peer managers (`PM2`) are strictly blocked (**Level 2 Isolation**).
  - **Task**: Can edit **any** Task belonging to their assigned activity (`Task A1`).

### 🌱 5. Field Officer (Field Data & Task Execution Tier)
- **Scope**: Task-level frontline execution.
- **Update Capabilities**:
  - **Project & Activity**: Read-only context.
  - **Task**: Can edit **only** tasks assigned directly to them (`custom_activity_owner == session.user`). Peer officers (`FO2`) are strictly blocked (**Level 3 Isolation**).
  - **Surveys**: Can create and edit surveys and activity outcomes submitted by them.
