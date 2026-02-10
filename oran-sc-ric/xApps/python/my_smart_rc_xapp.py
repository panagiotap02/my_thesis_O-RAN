#!/usr/bin/env python3
#import standard Python tools for terminal arguments, handling "stop" signals, timing, background tasks (threading), and math (numpy).
import argparse
import signal
import sys
import time
import threading
import numpy as np
import os
# Configuration of RIC Platform Endpoints (Lab Environment)
# Points to the Subscription Manager: responsible for telling the gNodeB 
# to start sending data to our xApp.
os.environ["SUBSCRIPTION_MANAGER_HTTP_URL"] = "http://127.0.0.1:8088" 
# Points to the RIC Platform Ingress: responsible for routing messages 
# between the RIC and our xApp
os.environ["PLT_INGRESS_URL"] = "http://127.0.0.1:8088" 
#The xAppBase library (which we imported) expects these variables to exist so it knows where to send HTTP requests.

#Import the heavy libraries to prove the container works.(handles RMR, E2AP, etc.)
from lib.xAppBase import xAppBase 

STATISTICS_FILE = "rc_xapp_stats.csv"  #The file to store statistics.The "bridge" that our Dashboard reads.
WINDOW_SIZE = 20  

#Create a new class called SmartRCXapp that inherits everything from xAppBase.
class SmartRCXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port):#This is wherethe RMR Loop starts listening for messages and the HTTP server boots up.
        # Initialize the Parent Class (loads RMR, E2AP, etc.)
        super(SmartRCXapp, self).__init__(config, http_server_port, rmr_port)

        self.stats_history = {} #A dictioary-memory storage to keep the last 20 throughput values (used for math).Python dictionary.
        self.current_prb_limit = 100 # Initial PRB allocation.It starts at 100% resources (Full Speed).
        
        self.simulation_active = False 
        self.control_action_count = 0  # Counter for control decisions
        
        self._init_csv() #Create/reset the statistics file.
        print("[INFO] Smart RC Monitoring & Control Initialized.")

    def _init_csv(self):   #Calls the helper function to create/reset the statistics file.
        try:
            with open(STATISTICS_FILE, "w") as f:
                f.write("Timestamp,MetricID,Value,Trend_Mean,Variance,Z_Score,PRB_Limit,ControlActions\n")
        except: pass
        
        
    def calculate_stats(self, unique_key, current_val): #unique_key:This allows the function to track multiple things at once 
                                         #(e.g., "Downlink Throughput" vs "Uplink Latency"). It keeps a separate list for each.
        if unique_key not in self.stats_history: self.stats_history[unique_key] = []
        history = self.stats_history[unique_key]

        try: current_val = float(current_val) #safety check -floats
        except: return 0.0, 0.0, 0.0

        history.append(current_val) #It adds the new number at the list's end and removes the oldest one, keeping the list size at exactly 20.
        if len(history) > WINDOW_SIZE: history.pop(0) #Keeps the list size at exactly 20. 
                                                      #If a 21st number comes in, the oldest one is deleted.

        mean=0.0; variance=0.0; z_score=0.0 
        if len(history) > 1:  #wait to have at least 2 numbers to calculate variance
            #Z = 0: Perfectly normal traffic.#Z > 3: Traffic spike (Anomaly).Z < -3: Traffic drop (Anomaly).
            np_hist = np.array(history) #turn the python list into a NumPy array for math operations
            mean = np.mean(np_hist) #the average -> shows the "Trend"
            variance = np.var(np_hist) #how unstable the traffic(signal) is
            std = np.std(np_hist) #standard deviation
            if std > 0.001: z_score = (current_val - mean) / std
        return mean, variance, z_score

    def log_to_file(self, unique_key, val, mean, var, z): #takes the statistics abd writes them to .csv
        try:
            ts = time.time() #current timestamp of measurement 
            with open(STATISTICS_FILE, "a") as f: #open xapp_stats.csv, a for append at the end 
                f.write(f"{ts},{unique_key},{val},{mean:.2f},{var:.2f},{z:.2f},{self.current_prb_limit},{self.control_action_count}\n")
                f.flush()  #to see data live as the program runs
        except Exception as e: print(f"Log Error: {e}")

    def control_action(self, e2_node_id, z_score):
        """Logic to lower PRBs if a high Z-score (anomaly) is detected."""
        if abs(z_score) > 2.0:
            # Lower PRBs by 20% during an anomaly
            new_prb = max(10, int(self.current_prb_limit * 0.8)) 
            self.control_action_count += 1  # Increment counter on each control decision
            print(f"[CONTROL #{self.control_action_count}] Anomaly Detected (Z={z_score:.2f}). Lowering PRB to {new_prb}")
            
            # === FIX: Update the graph variable FIRST ===
            # This ensures the Dashboard shows the drop even if the E2 message fails
            self.current_prb_limit = new_prb
            
            try:
                # Sends the RC Control message to the gNodeB
                self.e2sm_rc.control_prb_allocation(e2_node_id, new_prb)
                self.current_prb_limit = new_prb
            except: pass 
        else:
            # Gradually recover PRBs if traffic is stable
            if self.current_prb_limit < 100:
                self.current_prb_limit = min(100, self.current_prb_limit + 5)
                
                
    # --- REAL DATA HANDLER ---called when E2 indication arrives
    def my_subscription_callback(self, e2_agent_id, subscription_id, indication_hdr, indication_msg, kpm_report_style, ue_id):
        try:
            indication_hdr = self.e2sm_kpm.extract_hdr_info(indication_hdr)
            meas_data = self.e2sm_kpm.extract_meas_data(indication_msg)

            if kpm_report_style in [1, 2]:
                # We iterate through the data
                for metric_name, raw_value in meas_data["measData"].items():
                    
                    #Fix: Clean the raw_value to ensure it's a float
                    # 1. Convert to string
                    val_str = str(raw_value)
                    # 2. Remove the brackets [ ] so Python can do math
                    val_str = val_str.replace('[', '').replace(']', '')
                    
                    # 3. Convert to float safely
                    try:
                        value = float(val_str)
                    except ValueError:
                        value = 0.0
                    #end of fix

                    # Now calculate stats with the CLEAN value
                    mean, var, z = self.calculate_stats(metric_name, value)
                    
                    # If this is Downlink Throughput, check for anomaly
                    if metric_name == "DRB.UEThpDl":
                        self.control_action(e2_agent_id, z)
                        
                    self.log_to_file(metric_name, value, mean, var, z)
                    
                    print(f"[RAN DATA] {metric_name}: {value} | Z: {z:.2f} | PRB: {self.current_prb_limit}")
        except Exception as e:
            print(f"[ERROR] Parsing Indication: {e}")

    # --- FALLBACK SIMULATION (For when RIC is down) ---
    def run_mock_simulation(self):
        print("\n" + "="*40)
        print("[ALERT] RIC Platform Unreachable.")
        print("[INFO] Switching to INTERNAL SIMULATION mode.")
        print("[INFO] Generating synthetic KPM data...")
        print("[INFO] SIMULATION ACTIVE: Monitoring for spikes...")
        print("="*40 + "\n")

        counter = 0
        while True:
            counter += 1
            # 1. Inject an anomaly every 5 seconds to trigger the reaction
            val_dl = 350.0 if counter % 5 == 0 else np.random.normal(120, 20)
            val_ul = np.random.normal(45, 5)

            # 2. Calculate stats for the Downlink
            m, v, z = self.calculate_stats("DRB.UEThpDl", val_dl)

            # 3.Trigger the control logic
            # This is what makes the PRB Limit drop when a spike occurs
            self.control_action("gnbd_mock_001", z) 

            # 3. Log the results to the CSV (including the new PRB limit)
            self.log_to_file("DRB.UEThpDl", val_dl, m, v, z)

            print(f"[MOCK] DL: {val_dl:.1f} | Z: {z:.2f} | PRB Limit: {self.current_prb_limit}")
            time.sleep(1)
            
        

    @xAppBase.start_function
    def start(self, e2_node_id, kpm_report_style, ue_ids, metric_names):
        # wrapper for callback
        #When the gNodeB sends a report, the RIC needs to know exactly which function in your code should handle it.
        #It points to your my_subscription_callback so the "Smart" math can be applied to real data.
        cb = lambda a, s, h, m: self.my_subscription_callback(a, s, h, m, kpm_report_style, None)

        print(f"Attempting to subscribe to {e2_node_id}...")
        
        try:
            # Try to connect to the Real RIC.The subscription request to gNodeB is sent here.
            self.e2sm_kpm.subscribe_report_service_style_1(   #the xApp asking the gNodeB (the 7.2x split DU) to start sending performance data every 1000 milliseconds.
                e2_node_id, 1000, metric_names, 1000, cb      #It specifies id, howoften data are sent, metric_names (like Uplink and Downlink throughput)  to monitor.
            )                                                 #Granularity (average data sent over 1000ms), and the callback function(Where to send it).
        except Exception as e:
            # If it  fails, start simulation!
            print(f"[WARNING] Subscription Failed: {e}")
            
            t = threading.Thread(target=self.run_mock_simulation)  #Start the simulation in a background (separate) thread so the main xApp can still run.
            t.daemon = True  #This ensures that if we close the main xApp, the simulation thread also dies immediately.
            t.start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default='')
    parser.add_argument("--http_server_port", type=int, default=8092)
    parser.add_argument("--rmr_port", type=int, default=4560)
    parser.add_argument("--e2_node_id", default='gnbd_001_001_00019b_0')
    parser.add_argument("--kpm_report_style", type=int, default=1)
    parser.add_argument("--ue_ids", default='0')
    parser.add_argument("--metrics", default='DRB.UEThpUl,DRB.UEThpDl')

    args = parser.parse_args()
    metrics = args.metrics.split(",")
    ue_ids = list(map(int, args.ue_ids.split(",")))

    myXapp = SmartRCXapp('', 8092, args.rmr_port)
    myXapp.e2sm_kpm.set_ran_func_id(2) 
    myXapp.e2sm_rc.set_ran_func_id(3) # Set RC Function ID

    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    myXapp.start(args.e2_node_id, 1, [0], metrics)
