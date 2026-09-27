# 🚜 Krushi Vikas - Project Flow User Journey

This document outlines the **End-to-End Project Flow** across all user tiers in the Krushi Vikas platform. It specifies **what each user role sees and does on every screen** throughout the project lifecycle, incorporating screenshots from the `images/` directory.

*(Note: The standalone Activity Form is owned and documented separately by our teammate; this document focuses strictly on the Project Form, Project Activities Table, Baseline Surveys, and Project Governance.)*

---

## 🔒 1. Core Visibility Rule (Below-CXO Isolation)

To ensure operational focus and data isolation, project visibility in list views and search queries is governed by the following hierarchy rule:

```mermaid
flowchart TD
    ROLE{"User Role Tier"}
    
    ROLE -->|"👑 CXO Tier (CEO / Project Director / Admin)"| ALL["🌐 Universal Visibility<br/><i>Can see ALL projects across the organization</i>"]
    
    ROLE -->|"👥 Below-CXO Tier (Coordinator / Manager / Officer)"| CHECK{"Is the project or any subtask/activity assigned to you?"}
    
    CHECK -->|"YES"| VIEW["👁️ Allowed to View Project<br/><i>• Project assigned directly to user<br/>• OR Project activity assigned to user<br/>• OR Project subtask assigned to user</i>"]
    CHECK -->|"NO"| HIDE["⛔ Hidden / Access Denied<br/><i>Project is completely hidden from lists & search</i>"]
```

* **👑 CXO Tier (CEO, Project Director, System Manager, Administrator)**: Full cross-organization visibility of all projects.
* **📋 Project Coordinator**: Only sees projects assigned to them under their oversight (`project_coordinator == session.user`) or projects where a subtask is assigned to them.
* **⚙️ Project Manager**: Only sees the project assigned to them (`project_manager == session.user`) or projects where an activity/subtask is assigned to them.
* **🌱 Field Officer**: Only sees projects where an activity or subtask is assigned to them (`custom_activity_owner == session.user` / linked Employee or `assignee == session.user`). Unrelated projects do not appear in their list.

---

## 🗺️ 2. Project Flow Lifecycle Diagram

```mermaid
flowchart LR
    A["1. Project Initiation<br/><i>(+ Create Project button)</i>"] --> B["2. Project Creation Form<br/><i>(Assign Coordinator & Manager)</i>"]
    B --> C["3. Project Form & Financials<br/><i>(Budget, Actuals, Remaining Funds)</i>"]
    C --> D["4. Activities Table Setup<br/><i>(Define in Project Form)</i>"]
    D --> E["5. Baseline Survey Linking<br/><i>(Link Survey to Project)</i>"]
    E --> F["6. Ground Execution & Monitoring<br/><i>(Track Milestones to Completion)</i>"]

    classDef step fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    class A,B,C,D,E,F step;
```

---

## 👤 3. Step-by-Step Journey for Each User Type

---

### 👑 User Journey 1: CXO Tier (CEO / Project Director / Admin)

#### 1. What CXOs See:
* **Project Directory (`/app/kv-project`)**: Sees **every project** in the organization across all thematic areas, coordinators, and managers.
* **`+ Create Project` Action**: Active button in the top action bar.
* **Project Details Form**: Complete edit and delete capabilities. Full visibility into approved budgets, actual amounts spent, and remaining funds across all projects.

#### 2. What CXOs Do:
1. **Initiate Strategic Projects**: Create high-level organizational projects and assign the responsible Project Coordinator and Project Manager.
2. **Budget & Scope Governance**: Reallocate funds, revise timelines, and approve major project phase changes (*Planning* ➔ *Execution* ➔ *Results*).
3. **Cross-Project Reviews**: Monitor aggregated survey submissions and thematic performance metrics across all regional clusters.

---

### 📋 User Journey 2: Project Coordinator (Regional In-Charge & Overseer)

The Project Coordinator oversees a portfolio of projects, ensuring multi-project alignment and supporting Project Managers.

```mermaid
flowchart TD
    PC1["1. Access Project List<br/><i>(Sees only overseen projects)</i>"] --> PC2["2. Click '+ Create Project'<br/><i>(Initiates project setup)</i>"]
    PC2 --> PC3["3. Fill Project Parameters<br/><i>(Assign self as Coordinator, select PM)</i>"]
    PC3 --> PC4["4. Review Financial Tracking<br/><i>(Monitor Budget & Remaining Funds)</i>"]
    PC4 --> PC5["5. Oversee Activities Table<br/><i>(Validate scope & deliverables)</i>"]
    PC5 --> PC6["6. Verify Baseline Surveys<br/><i>(Ensure target benchmark is linked)</i>"]
```

#### Screen 1: Project Initiation (`+ Create Project`)
* **What the Coordinator Sees**: Navigates to `/app/kv-project`. In the top toolbar, the **`+ Create Project`** button is prominently visible.
* **What the Coordinator Does**: Clicks **`+ Create Project`** to launch a new project initiative for their region.

![Create Project Button](../images/create-project-button.png)
*Figure 1: Project List view with the '+ Create Project' action button visible to authorized users.*

---

#### Screen 2: Project Creation Form
* **What the Coordinator Sees**: A clean form requiring core project parameters:
  * **Project Name**: Name of the developmental initiative.
  * **Theme**: Thematic area link (e.g., *Sustainable Agriculture*, *Water Harvesting*).
  * **Project Phase** & **Status**: Defaulted to *Execution* / *In Progress*.
  * **Mandatory Project In-Charges**:
    * **`Project Coordinator`**: Pre-filled/selected with their user profile.
    * **`Project Manager`**: Mandatory field to designate the project owner.
  * **Timeline**: Start Date and End Date.
  * **Budget (INR)**: Total sanctioned allocation.
* **What the Coordinator Does**: Enters the project scope, assigns themselves as the supervising **Project Coordinator**, selects the designated **Project Manager**, enters the sanctioned budget, and clicks **Save**.

![Project Creation Form](../images/project-creation-form.png)
*Figure 2: KV Project Creation Form showing mandatory Project Coordinator & Project Manager selection, timeline, and budget.*

---

#### Screen 3: Project Detail & Financial Monitoring
* **What the Coordinator Sees**:
  * An active project form with dynamic financial cards:
    * **Budget (INR)**: Sanctioned budget.
    * **Actual Amount Spent (INR)**: Total expenditure logged to date.
    * **Remaining Funds (INR)**: Automatically computed (`Budget - Actual Spent`).
  * Action buttons in top header: **`View Activities`**, **`View Tasks`**, and **`Linked Forms`**.
  * If the Coordinator accidentally navigates to a project overseen by a *peer coordinator*, it opens in **Read-Only** mode.
* **What the Coordinator Does**: Reviews financial burn rate, checks whether remaining funds are sufficient for future milestones, and verifies timelines.

![Project Detail & Financial Tracking](../images/project-detail-financial-form.png)
*Figure 3: Project detail form with real-time financial tracking and role assignments.*

---

#### Screen 4: Activities Oversight in Project Form
* **What the Coordinator Sees**: The **Activities Section** table inside the project form showing all planned activities, budget per activity, start/end dates, and assigned owners.
* **What the Coordinator Does**: Evaluates whether the Project Manager has broken down the project appropriately across all quarters.

![Project Activities Section](../images/project-form-activities-section.png)
*Figure 4: Activities section in Project Form showing activity breakdown and child table.*

---

#### Screen 5: Linking Baseline Surveys
* **What the Coordinator Sees**: Under **Linked Structural Forms**, the **`Linked Baseline Form`** field.
* **What the Coordinator Does**: Validates that a comprehensive village/household baseline survey is linked to the project before full fund disbursement.

![Add Baseline Survey to Project](../images/add-baseline-survey-to-project.png)
*Figure 5: Linking an existing Baseline Survey to the Project.*

---

### ⚙️ User Journey 3: Project Manager (Direct Project Owner & Operational Lead)

The Project Manager directly owns the project assigned to them, driving day-to-day execution, budgeting, and activity management.

```mermaid
flowchart TD
    PM1["1. Open Assigned Project<br/><i>(Only assigned projects visible)</i>"] --> PM2["2. Track Financials & Budget<br/><i>(Log actual spend & monitor remaining)</i>"]
    PM2 --> PM3["3. Add Activities to Project<br/><i>(Populate activities child table)</i>"]
    PM3 --> PM4["4. Assign Activity Leads<br/><i>(Designate assignee & outputs)</i>"]
    PM4 --> PM5["5. Link Baseline Survey<br/><i>(Attach survey for benchmark)</i>"]
    PM5 --> PM6["6. Drive Project to Completion<br/><i>(Update phase to Results/Feedback)</i>"]
```

#### Screen 1: Project List View (Focused Visibility)
* **What the Project Manager Sees**: On `/app/kv-project`, only the project(s) assigned to them (`project_manager == session.user`) or projects containing subtasks assigned to them appear in the list. Unrelated projects are completely hidden.
* **What the Project Manager Does**: Clicks on their project to enter the management workspace. (They can also click **`+ Create Project`** if initiating a new project assigned to their unit).

---

#### Screen 2: Financial Management & Budget Utilization
* **What the Project Manager Sees**:
  * Sanctioned **Budget (INR)**.
  * Editable **Actual Amount Spent (INR)**.
  * **Remaining Funds (INR)**: Real-time read-only balance that updates instantly as actual expenses are entered.
* **What the Project Manager Does**: Inputs actual ground expenditures (equipment, training kits, materials) and monitors remaining balance to prevent cost overruns.

---

#### Screen 3: Setting Up Activities in the Project Form
* **What the Project Manager Sees**: The embedded **Activities** child table in the Project Form.
* **What the Project Manager Does**:
  1. Clicks **Add Row** in the Activities table.
  2. Enters the **Activity Name**, **Goal**, **Planned Budget**, **Start Date**, and **End Date**.
  3. Sets the **Assignee** (the Project Manager or designated lead).
  4. Specifies expected **Input/Output** (e.g., *"10 Training Kits"*, *"100% participation"*).
  5. Clicks **Save**. The activity is now part of the project execution plan.

![Activity Added in Project Form](../images/activity-added-in-project-form-and-assigned-to-pm_test.png)
*Figure 6: Activity added directly within the Project Form child table and assigned to the Project Manager.*

---

#### Screen 4: Linking Baseline Survey & Structural Forms
* **What the Project Manager Sees**: The **Linked Structural Forms** section on the Project Form.
* **What the Project Manager Does**:
  1. Selects the verified **Baseline Survey** from the dropdown link field.
  2. Clicks **Save**.
  3. Uses the **`Baseline Survey`** button in the top action toolbar (`Linked Forms` menu) to quickly jump to the survey record.

---

### 🌱 User Journey 4: Field Officer (Task Executor & Ground Surveyor)

The Field Officer operates on the ground, interacting with farmers, collecting survey data, and executing assigned subtasks.

```mermaid
flowchart TD
    FO1["1. Filtered Project Access<br/><i>(Only sees projects with assigned subtasks)</i>"] --> FO2["2. Read-Only Project View<br/><i>(Inspects goals, dates & villages)</i>"]
    FO2 --> FO3["3. Create Baseline Survey<br/><i>(Records household & farm data)</i>"]
    FO3 --> FO4["4. Submit Survey Data<br/><i>(Syncs with parent project benchmark)</i>"]
    FO4 --> FO5["5. Execute Assigned Subtasks<br/><i>(Updates status to Completed)</i>"]
```

#### Screen 1: Filtered Project List View
* **What the Field Officer Sees**:
  * When opening `/app/kv-project`, they **only see projects where an activity or subtask is assigned to them**.
  * All other projects are invisible, keeping the officer focused exclusively on their target operational area.
  * The `+ Create Project` button is **hidden**.
* **What the Field Officer Does**: Selects their assigned project to inspect objectives, target villages, and timelines.

---

#### Screen 2: Project Detail View (Read-Only)
* **What the Field Officer Sees**:
  * The Project Form opens in **Read-Only** mode.
  * Financial totals, timelines, and activity scopes are visible for context, but all edit fields are disabled.
* **What the Field Officer Does**: Reviews project parameters and planned activities before going to the field.

---

#### Screen 3: Conducting & Submitting Baseline Surveys
* **What the Field Officer Sees**: The **Baseline Survey Creation Form** (`/app/baseline-survey/new` or `/village_profile`).
  * **Farmer Identification**: Farmer Name, Contact, Village, Aadhaar/ID.
  * **Household Demographics**: Family members, annual household income.
  * **Agricultural & Landholding Profile**: Total land, irrigated acreage, water source, current crops.
  * **Benchmark Survey Questions**: Categorized questions regarding farming practices and irrigation methods.
* **What the Field Officer Does**:
  1. Enters field data collected directly from household interviews.
  2. Submits the survey record.
  3. The survey is then available for the Project Manager to link directly to the KV Project.

![Create Baseline Survey Form](../images/create-baseline-survey-form.png)
*Figure 7: Baseline Survey Form for recording household demographics, agricultural profile, and baseline metrics.*

---

## 📊 4. Comparative Matrix: What Each User Sees & Does

| Project Screen / Action | 👑 CXO Tier | 📋 Project Coordinator | ⚙️ Project Manager | 🌱 Field Officer |
| :--- | :--- | :--- | :--- | :--- |
| **`+ Create Project` Action** *(Fig. 1)* | ✅ Visible & Active | ✅ Visible & Active | ✅ Visible & Active | ⛔ Hidden |
| **Project Creation Form** *(Fig. 2)* | Create any project; assign Coordinator & PM | Create project; assign self as Coordinator & select PM | Create project; assign self as PM & select Coordinator | ⛔ Access Denied |
| **Project List View** | All org projects visible | Only overseen projects or projects with subtasks | Only assigned projects or projects with subtasks | Only projects with assigned subtasks/activities |
| **Project Detail & Financials** *(Fig. 3)* | Edit / Delete any project across org | Edit all overseen projects (Peer projects read-only) | Edit assigned project; log actual spend & track remaining funds | 👁️ Read-Only access to project context |
| **Project Activities Table** *(Fig. 4 & 6)* | Full edit on any project's activities | Review & edit activities under overseen projects | Add activity rows, set planned budgets & assign leads | 👁️ Read-Only view of activity list |
| **Baseline Survey Linking** *(Fig. 5)* | Link or unlink any survey | Review & validate linked survey | Link approved baseline survey to the project | 👁️ Read-Only on project link |
| **Baseline Survey Creation** *(Fig. 7)* | View all survey submissions | Review surveys in regional cluster | Review surveys in assigned project | Fill out & submit surveys during field visits |

---

## 📁 5. Screenshot Asset Mapping

| Screenshot File | Caption / Document Context | Primary User Who Interacts |
| :--- | :--- | :--- |
| `images/create-project-button.png` | **Figure 1**: Project List view showing the `+ Create Project` button in top toolbar | Project Coordinator / Project Manager / CXO |
| `images/project-creation-form.png` | **Figure 2**: Project creation form with mandatory Coordinator, Manager, and Budget | Project Coordinator / Project Manager |
| `images/project-detail-financial-form.png` | **Figure 3**: Active project form displaying Budget, Actual Spent, and Remaining Funds | Project Manager / Project Coordinator |
| `images/project-form-activities-section.png` | **Figure 4**: Activities section in the project form with child table and Add Row action | Project Manager / Project Coordinator |
| `images/activity-added-in-project-form-and-assigned-to-pm_test.png` | **Figure 6**: Activity row configured directly in the project form and assigned to PM | Project Manager |
| `images/create-baseline-survey-form.png` | **Figure 7**: Baseline survey form for recording village and household farmer data | Field Officer |
| `images/add-baseline-survey-to-project.png` | **Figure 5**: Attaching the approved Baseline Survey to the Project under Linked Forms | Project Manager / Project Coordinator |
