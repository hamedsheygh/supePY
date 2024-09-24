import psutil
import GPUtil
import time
import threading
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Function to get CPU and GPU usage for "example.exe"
def get_usage():
    cpu_usage = 0
    gpu_usage = 0
    # Look for process example.exe
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        if proc.info['name'] == 'game engine.exe':
            cpu_usage = proc.cpu_percent(interval=1)
    
    # Get GPU usage
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu_usage = gpus[0].load * 100  # GPU load in percentage
    
    return cpu_usage, gpu_usage

# Function to update graph dynamically
def update_graph():
    while True:
        cpu, gpu = get_usage()
        x_data.append(len(x_data))
        cpu_data.append(cpu)
        gpu_data.append(gpu)
        
        # Update plot
        ax.clear()
        ax.plot(x_data, cpu_data, label='CPU Usage (%)')
        ax.plot(x_data, gpu_data, label='GPU Usage (%)')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Usage (%)')
        ax.legend(loc='upper right')
        
        # Update canvas
        canvas.draw()

        time.sleep(1)

# Create custom Tkinter window
app = ctk.CTk()
app.geometry("600x400")
app.title("CPU and GPU Usage Monitor")

# Graph initialization
fig, ax = plt.subplots()
x_data, cpu_data, gpu_data = [], [], []

# Embed graph in Tkinter window
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)
canvas.draw()

# Start a separate thread to update the graph
thread = threading.Thread(target=update_graph, daemon=True)
thread.start()

# Run the application
app.mainloop()
