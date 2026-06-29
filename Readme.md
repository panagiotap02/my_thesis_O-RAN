Experimental Deployment of an End-to-End O-RAN Testbed with xApp Development for Dynamic Radio Resource Management and 5G Network Decongestion🎓 Diploma Thesis | University of PatrasDepartment of Electrical and Computer EngineeringAuthor: Panagiota Panagiotopoulou (A.M. 1083759)Supervisor: Prof. Spyridon DenazisCo-Examiners: Prof. Alexios Birbas, Prof. Odysseas KoufopavlouDefense Date: February 2026📝 Project OverviewThis repository hosts the implementation of a complete, disaggregated, software-based 5G Standalone (SA) network following the O-RAN Alliance specifications[cite: 1, 2].The core contribution of this thesis is the Smart RC xApp, an intelligent control application executing within a Near-Real-Time RAN Intelligent Controller (Near-RT RIC) platform[cite: 1, 2]. By continuously monitoring real-time Downlink Throughput ($DRB.UEThpDl$) via the E2 interface, the xApp implements a closed-loop control mechanism utilizing a rolling Z-Score anomaly detection algorithm[cite: 1, 2]. Upon detecting sudden traffic spikes, it proactively mitigates congestion by dynamically adjusting physical resource constraints (PRB Throttling) on the gNodeB's MAC Scheduler, ensuring Quality of Service (QoS) and Quality of Experience (QoE) stability[cite: 1, 2].📺 Watch the Live Demo Video on YouTube[cite: 1]🏗️ System Architecture & Hybrid Functional SplitThe experimental testbed disaggregates the traditional monolithic RAN into standard-compliant entities distributed across cloud VMs and local edge hardware:5G Core Network (5GC): Powered by Open5GS running on a Cloud VM (Ubuntu Server). Subscriber database profiles are stored in MongoDB and provisioned via a custom WebUI accessed using secure SSH Tunneling[cite: 1, 2].O-RAN gNodeB: Built using the srsRAN Project, disaggregated into a Centralized Unit (O-CU) and a Distributed Unit (O-DU), embedding a native E2 Agent[cite: 1, 2].Open Radio Unit (O-RU): Handled by an Ettus USRP B210 Software Defined Radio (SDR) transceiver connected via a high-speed USB 3.0 interface[cite: 1, 2].Near-RT RIC: Deployed via Docker Compose containers (O-RAN SC platform microservices), facilitating low-latency routing through the RMR (RIC Message Router) bus[cite: 1, 2].🔀 The Hybrid Functional Split ApproachTo overcome local FPGA limitations on SDR hardware while maintaining granular scheduling control, we developed a hybrid split architecture:Split 7.2x (Logical Layer - High-PHY / MAC): All scheduling decisions and high-level physical layer processing are executed in software (O-DU CPU)[cite: 1, 2]. This enables the xApp to dynamically intercept and alter the MAC Scheduler parameters in near-real-time[cite: 1, 2].Split 8 (Physical/Transport Layer - Low-PHY / RF): Time-domain baseband I/Q samples are transferred via USB 3.0 from the workstation (emulating Low-PHY in software) to the USRP B210, which handles raw RF transmission over 5G NR Band n78 (3.5 GHz TDD) with a 20 MHz bandwidth[cite: 1, 2].🧠 Smart RC xApp Closed-Loop LogicThe xApp orchestrates a low-latency MAPE-K (Monitor-Analyze-Decide-Act) loop[cite: 1, 2]:       +--------------------------------------------+
       |                  Near-RT RIC               |
       |  +------------------+   +---------------+  |
       |  |   Smart RC xApp  |-->|  Redis DBaaS  |  |
       |  +------------------+   +---------------+  |
       |         ^        |                         |
       |         | KPM    | RC                      |
       |         | (12050)| (12040)                 |
       +---------|--------|-------------------------+
                 |        v
       +---------|--------|-------------------------+
       |    E2   |        | srsRAN gNodeB           |
       |  +------|--------v-----+                   |
       |  |       E2 Agent      |                   |
       |  +---------------------+                   |
       |  |    O-CU (Control)   |                   |
       |  +---------------------+                   |
       |  |   O-DU (Scheduler)  |                   |
       +--+---------------------+-------------------+
1. Monitor (E2SM-KPM)The xApp establishes an E2 Subscription ($RIC\_SUB\_REQ$) to the O-DU's E2 Agent[cite: 1, 2]. The gNodeB continuously measures the downlink user throughput ($DRB.UEThpDl$) at a granularity period of 1000ms and streams it back to the xApp via $RIC\_INDICATION$ (RMR type 12050) packets[cite: 1, 2].2. Analyze (Sliding Window & Z-Score)Incoming measurements ($x_i$) are pushed to a First-In-First-Out (FIFO) Sliding Window list storing exactly the $20$ most recent samples[cite: 1, 2]. The xApp computes the rolling mean ($\mu$) and standard deviation ($\sigma$) to derive the statistical Z-Score:$$Z_{score} = \frac{x_i - \mu}{\sigma}$$This allows the xApp to dynamically distinguish between normal network jitter (within-limit noise) and actual traffic anomalies[cite: 1, 2].3. Decide & Act (E2SM-RC)Congestion State: If the condition $|Z_{score}| > 2.0$ is met, a traffic spike (anomaly) is detected[cite: 1, 2]. The xApp immediately calculates a throttled PRB threshold:$$\text{New PRB Limit} = \max\left(10, \lfloor \text{Current Limit} \times 0.8 \rfloor\right)$$This value is wrapped into an E2SM-RC Control Message (Format 1 encoded via ASN.1 PER rules) and dispatched over the E2 interface as an RMR 12040 (RIC_CONTROL_REQ)[cite: 1, 2].Recovery State: When the Z-Score returns to the $[-2.0, 2.0]$ range, the scheduler gradually restores resources in incremental steps of $+5$ PRBs per cycle until it reaches full capacity ($100\%$)[cite: 1, 2].📂 Repository Structuremy_thesis_O-RAN/
├── oran-sc-ric/             
│   ├── xApps/
│   │   └── python/            
│   │       ├── my_smart_rc_xapp.py      # Main xApp with Z-Score & MAPE-K logic
│   │       ├── live_dashboard.py        # WebAgg browser-based dynamic dashboard
│   │       ├── e2sm_kpm_module.py       # Helper lib for E2SM-KPM (encoding/decoding)
│   │       └── e2sm_rc_module.py        # Helper lib for E2SM-RC (encoding/decoding)
│   ├── docker-compose.yml      # Orchestrates isolated Near-RT RIC microservices
│   └── configs/                # Static RMR table configurations (routes.rtg)
│
├── srsRAN_Project/              # CU/DU open-source implementation
│   └── configs/
│       └── tested_configs/      
│           ├── cu_E2.yml                       # O-CU config mapped to Open5GS AMF
│           └── du_rf_b200_tdd_n78_20mhz_E2.yml  # O-DU config with E2 Agent & USRP params
│
├── core/                        # Open5GS Core Network customizations
│   └── etc/
│       └── open5gs/             
│           ├── amf.yaml         # AMF service settings (PLMN, TAC: 100, N2 Bindings)
│           └── upf.yaml         # UPF service settings (N3 bindings and NAT)
│
└── README.md                    
This research implementation leverages and extends the following outstanding open-source projects:Open5GS Core Network Release Repository[cite: 1]srsRAN Software Radio Systems 5G Suite[cite: 1]O-RAN Software Community (OSC) Near-RT RIC Integration[cite: 1]⚙️ System RequirementsHardware InfrastructureEntitySpecificationsRoleLab WorkstationDell OptiPlex 7060, Intel i7-8700 CPU, 16GB RAM, Ubuntu 22.04 LTSHosts srsRAN gNodeB, Near-RT RIC, and xAppsCore Network VMCloud Instance / Separate VM, 2 vCPUs, 4GB RAM, Ubuntu ServerHosts Open5GS Control/User plane microservicesSoftware Defined Radio (SDR)Ettus USRP B210 with USB 3.0 interface connectivityFunctions as the physical O-RUCOTS User EquipmentSamsung Galaxy A17 5GCommercial terminal for over-the-air validationTest SIMProgrammable USIM (configured with IMSI, K, OPc matching Core)Subscriber authentication credentialSoftware StackSoftwareRequired VersionRoleDocker Enginev20.10+Container runtime engine for isolated RIC microservicesDocker Composev2.0+Orchestrates the multi-container RIC platformPythonv3.8+Runtime environment for xApp logic and Matplotlib WebAggOpen5GSv2.7+Production-grade 5G Standalone Core NetworksrsRAN Projectv23.10+5G gNodeB (O-CU/O-DU) with built-in E2 AgentMongoDBv8.0+NoSQL subscriber profile database store for Open5GSUHD Driverv4.5+Low-level drivers and API for Ettus USRP hardware🚀 Startup & Execution GuideFollow these steps in the exact sequential order to ensure proper synchronization between disaggregated control planes.1. Initialize the 5G Core Network (Open5GS)Connect via SSH to your Cloud Core Network VM, start all services, and verify the AMF state:# Restart all Open5GS systemd services
sudo systemctl restart open5gs-amfd open5gs-smfd open5gs-upfd open5gs-nrfd open5gs-ausfd open5gs-udmd open5gs-udrd open5gs-pcfd open5gs-nssfd open5gs-bsfd open5gs-scpd

# Verify the N2 control plane supervisor endpoint is healthy
sudo systemctl status open5gs-amfd
2. Deploy the Near-RT RIC PlatformOn the local Lab Workstation, spin up the Docker-compose multi-container stack:cd ~/clean/oran-sc-ric
docker compose down
docker compose up -d
docker ps
3. Spin Up srsRAN gNodeB (O-CU & O-DU)Open two separate terminals on your local Lab Workstation.Terminal 1 (O-CU Platform):cd ~/clean/srsRAN_Project/build/apps/cu
sudo ./srscu -c /home/panagiotopoulou/clean/srsRAN_Project/configs/tested_configs/cu_E2.yml
Terminal 2 (O-DU Layer & USRP B210 Connection):cd ~/clean/srsRAN_Project/build/apps/du
sudo ./srsdu -c /home/panagiotopoulou/clean/srsRAN_Project/configs/tested_configs/du_rf_b200_tdd_n78_20mhz_E2.yml
4. Execute the Smart Control xAppAttach to the running RIC network and run the Python xApp inside the runner container:cd /home/panagiotopoulou/clean/oran-sc-ric
docker compose exec python_xapp_runner ./my_smart_rc_xapp.py --metrics=DRB.UEThpDl,DRB.UEThpUl --kpm_report_style=1
5. Launch the Real-Time Reporting DashboardRun the visualizer script locally to start the WebAgg server:cd /home/panagiotopoulou/clean/oran-sc-ric/xApps/python
python3 live_dashboard.py
🌐 Access the Live Charting View: Open your browser and navigate to http://127.0.0.1:8988 to monitor real-time throughput metrics, rolling variance, Z-score thresholds, and active PRB throttling states.📂 References & Upstream ImplementationsOpen5GS Core Network Release Repository[cite: 1]srsRAN Software Radio Systems 5G Suite[cite: 1]O-RAN Software Community (OSC) Near-RT RIC Integration[cite: 1]📬 ContactPanagiota PanagiotopoulouLinkedIn: [Your LinkedIn Profile Link]Email: [Your Email Address]
