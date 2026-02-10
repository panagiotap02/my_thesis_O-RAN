import os #to check if the CSV file exists,before reading it
import pandas as pd #to read the CSV data and organize them into a table for easy plotting
import matplotlib

# Use WebAgg for browser-based dynamic diagrams
matplotlib.use('WebAgg') 

import matplotlib.pyplot as plt
import matplotlib.animation as animation

# CONFIGURATION
STATISTICS_FILE = "rc_xapp_stats.csv"
WINDOW_SIZE = 30
TARGET_METRIC = "DRB.UEThpDl"

# Create the figure with 5 subplots
fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(12, 16), sharex=True)
plt.style.use('ggplot') # Using a universal style to avoid FileNotFoundError

#add empty space at the bottom so "Time" isn't cut off
plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1, hspace=0.3)

# --- INITIAL SETUP (So labels are always visible) ---
ax1.set_title(f"Live RAN Traffic: {TARGET_METRIC}", fontsize=12, fontweight='bold')
ax1.set_ylabel("Mbps")
ax1.grid(True, alpha=0.3)

ax2.set_ylabel("Variance")
ax2.grid(True, alpha=0.3)

ax3.set_ylabel("Z-Score")
ax3.set_ylim(-3, 3)
ax3.grid(True, axis='y', alpha=0.3)
ax3.axhline(y=2.0, color='grey', linestyle='--', alpha=0.5)
ax3.axhline(y=-2.0, color='grey', linestyle='--', alpha=0.5)

ax4.set_ylabel("Resources (%)")
ax4.set_ylim(0, 110)
ax4.grid(True, alpha=0.3)

ax5.set_ylabel("Control Actions")
ax5.set_xlabel("Time (Samples)", fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.3)

# --- ANIMATION PART ---
def animate(i):
    if not os.path.exists(STATISTICS_FILE):
        ax1.set_title("Waiting for data written in rc_xapp_stats.csv...")
        return

    try:
        # 1. Load Data
        try:
            # We explicitly name columns because your CSV doesn't have a header row
            df = pd.read_csv(STATISTICS_FILE, names=["Timestamp", "MetricID", "Value", "Trend_Mean", "Variance", "Z_Score", "PRB_Limit", "ControlActions"])
            if df.empty: return
        except: return
        
        # 2.Filter for the specific metric (e.g., Downlink Throughput)
        df = df[df['MetricID'] == TARGET_METRIC]
        
        df['Value'] = df['Value'].astype(str).str.replace(r'[\[\]]', '', regex=True) ## Convert "[0.0]" -> "0.0".Remove brackets 
        
        # Force columns to be numbers (Fixes "bad operand type for abs(): str")
        # If it finds text like "Value", it turns it into NaN (Not a Number)
        cols = ["Value", "Trend_Mean", "Variance", "Z_Score", "PRB_Limit", "ControlActions"]
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean data: remove rows with NaN values in critical columns
        df = df.dropna(subset=["Value", "Z_Score"])
        df = df.tail(WINDOW_SIZE)
        if len(df) < 2: return

        plot_index = range(len(df))

        # Panel 1: Throughput Value & Trend
        ax1.clear()
        # Adding .values converts Pandas Series to NumPy arrays to avoid the indexing error
        ax1.plot(plot_index, df["Value"].values, label="Real-Time Value", color="#00ffcc", linewidth=2)
        ax1.plot(plot_index, df["Trend_Mean"].values, label="Trend (Mean)", color="orange", linestyle="--")
        ax1.legend(loc="upper left")
        ax1.set_title(f"Live RAN Traffic: {TARGET_METRIC}", fontsize=12, fontweight='bold')
        ax1.set_ylabel("Mbps")
        ax1.grid(True, alpha=0.3)

        # Panel 2: Variance (Jitter)
        ax2.clear()
        ax2.plot(plot_index, df["Variance"].values, color="#ff66ff", linewidth=1.5)
        ax2.fill_between(plot_index, df["Variance"].values, color="#ff66ff", alpha=0.1)
        ax2.set_ylabel("Variance")
        ax2.grid(True, alpha=0.3)

        # Panel 3: Anomaly Score (Z-Score)
        ax3.clear()
        z_values = df["Z_Score"].values  # Convert Z_Score to numpy for the color logic
        colors = ['red' if abs(z) > 2 else '#99ff99' for z in z_values]
        ax3.bar(plot_index, z_values, color=colors, alpha=0.8)
        ax3.axhline(y=2.0, color='grey', linestyle='--', alpha=0.5)
        ax3.axhline(y=-2.0, color='grey', linestyle='--', alpha=0.5)
        ax3.set_ylabel("Z-Score")
        ax3.set_ylim(-3, 3) # Keep scale fixed
        ax3.grid(True, axis='y', alpha=0.3)
        
        # Panel 4: PRB Limit
        ax4.clear()
        # Plot PRB Limit as a thick green line (Stepped looks better for control changes)
        ax4.step(plot_index, df["PRB_Limit"].values, where='post', color="#2ca02c", linewidth=2.5, label="PRB Allocation")
        ax4.fill_between(plot_index, df["PRB_Limit"].values, step='post', color="#2ca02c", alpha=0.2)
        ax4.set_ylabel("Resources (%)")
        ax4.set_ylim(0, 110)
        ax4.legend(loc="lower left")
        ax4.grid(True, alpha=0.3)
        
        # Panel 5: Control Action Counter
        ax5.clear()
        ax5.plot(plot_index, df["ControlActions"].values, color="#ff6600", linewidth=2.5, marker='o', markersize=4, label="Control Decisions")
        ax5.fill_between(plot_index, df["ControlActions"].values, color="#ff6600", alpha=0.2)
        ax5.set_ylabel("Control Actions")
        ax5.legend(loc="upper left")
        ax5.grid(True, alpha=0.3)
        
        # Add current count as text annotation
        current_count = int(df["ControlActions"].values[-1]) if len(df) > 0 else 0
        ax5.annotate(f'Total: {current_count}', xy=(0.98, 0.85), xycoords='axes fraction',
                     fontsize=14, fontweight='bold', color='#ff6600',
                     ha='right', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # This label will now be visible because of 'bottom=0.1' above
        ax5.set_xlabel("Time (Samples)", fontsize=12, fontweight='bold')
        
        
    except Exception as e:
        print(f"Plotting Error: {e}")

# Set the animation to update every 1000ms (1 second)
ani = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)

plt.show()
