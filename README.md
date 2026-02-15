## Repository Structure

```text
my_thesis_O-RAN/
├── oran-sc-ric/               
│   ├── xApps/
│   │   └── python/            
│   │       ├── my_smart_rc_xapp.py      # Main xApp with Z-Score logic
│   │       ├── live_dashboard.py        # Real-time visualization dashboard
│   │       ├── e2sm_kpm_module.py       # Helper lib for E2SM-KPM (encoding/decoding)
│   │       └── e2sm_rc_module.py        # Helper lib for E2SM-RC (encoding/decoding)
│   ├── docker-compose.yml      # Docker Compose file to orchestrate the RIC containers
│   └── configs/                # Configuration files for RIC entities (e.g., routes.rtg)
│
├── srsRAN_Project/              # Customizations for the srsRAN gNB
│   └── configs/
│       └── tested_configs/      # Tested configuration files
│           ├── cu_E2.yml                      # O-CU configuration with E2 enabled
│           └── du_rf_b200_tdd_n78_20mhz_E2.yml # O-DU configuration for USRP B210 with E2 enabled
│
├── core/                         # Customizations for the Open5GS Core Network
│   └── etc/
│       └── open5gs/              # Modified core network configurations
│           ├── amf.yaml           # AMF configuration with PLMN, TAC, and network bindings
│           └── upf.yaml           # UPF configuration for N3 interface and NAT
│
└── README.md                     


This project is based on the following open source implementations:
1.Guide for installing and configuring Open5GS Core Network:
https://open5gs.org/  
https://open5gs.org/open5gs/docs/guide/01-quickstart/ (Open5GS Documentation)
2.SC-RIC integration for Near-RT RIC and example Python xApps:
https://github.com/srsran/oran-sc-ric
3.srsRAN Project: Implements the O-RAN gNodeB (O-CU and O-DU) with an embedded E2 Agent.
https://docs.srsran.com/en/latest/


The core contribution of this thesis, the my_smart_rc_xapp.py, runs on Near-RT RIC. It subscribes to Key Performance Measurements (KPMs) from the gNB via the E2 interface, 
analyzes downlink throughput (DRB.UEThpDl) using a Z-Score algorithm with a sliding window, and sends RAN Control (RC) messages to dynamically throttle Physical Resource
Blocks (PRBs) when congestion is detected.


Hardware Requirements:

Lab Workstation	Dell OptiPlex 7060 (or equivalent) with Intel Core i7-8700, 16GB RAM, Ubuntu 22.04
Core Network VM	Separate machine or VM with Ubuntu Server, 4GB+ RAM, IP: 10.1.6.206
SDR (O-RU)	USRP B210 with USB 3.0 connection
User Equipment (UE)	5G-compatible smartphone (e.g., Samsung Galaxy A17 5G)
SIM Card	Programmable SIM card with IMSI: 001010000000001

Software Requirements:

Software	       Version	    Purpose
Docker           20.10+  	    Container runtime for Near-RT RIC
Docker Compose	 2.0+	        Orchestration of RIC containers
Python	         3.8+	        For xApp development and dashboard
Open5GS	         2.7+	        5G Core Network
srsRAN Project	 23.10+	      O-RAN gNodeB with E2 Agent
MongoDB	         8.0+       	Subscriber database for Open5GS
UHD Drivers	     4.5+	        Drivers for USRP B210

---
 
## Startup Sequence (Execution Guide)
 
Follow the steps below in the exact order to ensure proper synchronization between the network entities.
 
 
### 1. Start the Core Network (Open5GS)
Connect to the Core Network VM (`ssh ubuntu@10.1.6.206`) and restart all services:
 
```bash
sudo systemctl restart open5gs-amfd open5gs-smfd open5gs-upfd open5gs-nrfd open5gs-ausfd open5gs-udmd open5gs-udrd open5gs-pcfd open5gs-nssfd open5gs-bsfd open5gs-scpd
```
 
Verification: Run this command to ensure the core amf service is active
```bash
sudo systemctl status open5gs-amfd
```
 
 # 2. Start Near-RT RIC
On the Lab Workstation (ssh panagiotopoulou@172.16.100.96), deploy the RIC:
```bash
cd ~/clean/oran-sc-ric
docker compose down
docker compose up -d
docker ps
```


### 3. Start srsRAN gNodeB (CU & DU)
Open two separate terminals on the Lab Workstation.

Terminal 1 (O-CU):
```bash
cd ~/clean/srsRAN_Project/build/apps/cu
sudo ./srscu -c /home/panagiotopoulou/clean/srsRAN_Project/configs/tested_configs/cu_E2.yml
```

Terminal 2 (O-DU):
```bash
cd ~/clean/srsRAN_Project/build/apps/du
sudo ./srsdu -c /home/panagiotopoulou/clean/srsRAN_Project/configs/tested_configs/du_rf_b200_tdd_n78_20mhz_E2.yml
```


### Commands to run an xApp
Requirement: The docker compose from /home/panagiotopoulou/clean/oran-sc-ric/docker-compose.yml must already be running (Step 2).
### Run the Smart Control xApp (Z-Score logic)
```bash
cd /home/panagiotopoulou/clean/oran-sc-ric
docker compose exec python_xapp_runner ./my_smart_rc_xapp.py --metrics=DRB.UEThpDl,DRB.UEThpUl --kpm_report_style=1
```

### Run the Live Dashboard
To see real-time visualization and throughput graphs:
```bash
cd /home/panagiotopoulou/clean/oran-sc-ric/xApps/python
python3 live_dashboard.py
```

### Access: Open your browser at http://127.0.0.1:8988



