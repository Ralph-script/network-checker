import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import ipaddress
import subprocess
import random
import threading

# OOP FORMAT
class ServerStatusChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Status Checker")
        self.root.geometry("860x450")

        self.projects = {}  # Dictionary to hold project data

        # Frame for controls
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(side=tk.TOP, fill=tk.X)

        # Load from CSV button
        load_csv_button = ttk.Button(frame, text="Load from CSV", command=self.load_from_csv)
        load_csv_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Project dropdown
        self.project_var = tk.StringVar()
        self.project_dropdown = ttk.Combobox(frame, textvariable=self.project_var, state="readonly")
        self.project_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        self.project_dropdown.bind("<<ComboboxSelected>>", self.display_project_servers)

        # Check IP statuses button
        check_status_button = ttk.Button(frame, text="Run", command=self.start_checking_status)
        check_status_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Treeview for displaying servers, IPs, and status
        self.tree = ttk.Treeview(self.root, columns=("Station", "Sensor", "IP", "Status"), show="headings")
        self.tree.heading("Station", text="Station")
        self.tree.heading("Sensor", text="Sensor")
        self.tree.heading("IP", text="IP Address")
        self.tree.heading("Status", text="Status")
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind right-click to the treeview items
        self.tree.bind("<Button-3>", self.on_right_click)

        # Configure tags for different status colors
        self.tree.tag_configure("Active", foreground="green")
        self.tree.tag_configure("Inactive", foreground="red")
        self.tree.tag_configure("Error", foreground="orange")
        self.tree.tag_configure("Checking", foreground="blue")

        # Progress bar for loading indication
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Check Again", command=self.check_again)
        self.context_menu.add_command(label="Tracert", command=self.click_tracert)

    def load_from_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, mode='r', newline='') as file:
                reader = csv.reader(file)
                self.projects.clear()
                last_project = None  # To hold the last known project name

                for i, row in enumerate(reader):
                    if i == 0:
                        continue  # Skip header row

                    project = row[0].strip() if row[0].strip() else last_project
                    server = row[1].strip()
                    sensor = row[2].strip()
                    ip = row[3].strip()

                    if project:
                        last_project = project

                    # Validate IP address
                    try:
                        ipaddress.ip_address(ip)
                    except ValueError:
                        continue

                    if not project or not server or not sensor or not ip:
                        continue

                    if project not in self.projects:
                        self.projects[project] = []
                    self.projects[project].append((server, sensor, ip))

                if self.projects:
                    self.project_dropdown['values'] = list(self.projects.keys())
                    self.project_var.set('')  # Reset dropdown selection
                else:
                    messagebox.showwarning("Warning", "No valid data found in CSV.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")

    def start_checking_status(self):
        # Start a new thread to check statuses
        thread = threading.Thread(target=self.check_ip_statuses)
        thread.start()
    def display_project_servers(self, event):
        selected_project = self.project_var.get()
        if not selected_project:
            return

        # Clear the treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Display servers and IPs for the selected project
        for server, sensor, ip in self.projects.get(selected_project, []):
            self.tree.insert("", "end", values=(server, sensor, ip, "Unknown"), tags=("Unknown",))

    # def check_ip_statuses(self):
    #     selected_project = self.project_var.get()
    #     if not selected_project:
    #         messagebox.showwarning("Warning", "No project selected.")
    #         return
    #
    #     # Set progress bar
    #     total_servers = len(self.tree.get_children())
    #     self.progress_bar["value"] = 0
    #     self.progress_bar["maximum"] = total_servers
    #
    #     # Check IP statuses for the selected project
    #     for idx, child in enumerate(self.tree.get_children()):
    #         server, sensor, ip, _ = self.tree.item(child, "values")
    #         # Set status to "Checking..."
    #         self.tree.item(child, values=(server, sensor, ip, "Checking..."), tags=("Checking",))
    #         self.root.update_idletasks()  # Update UI
    #
    #         status = self.ping_ip(ip)
    #         status = self.trace_route(ip)
    #         self.tree.item(child, values=(server, sensor, ip, status), tags=(status,))
    #
    #         # Update progress bar
    #         self.progress_bar["value"] += 1
    #         self.root.update_idletasks()
    #
    #     messagebox.showinfo("Info", "IP status check completed.")
    def check_ip_statuses(self):
        selected_project = self.project_var.get()
        if not selected_project:
            messagebox.showwarning("Warning", "No project selected.")
            return

        # Set progress bar
        total_servers = len(self.tree.get_children())
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = total_servers

        # Check IP statuses for the selected project
        for idx, child in enumerate(self.tree.get_children()):
            server, sensor, ip, _ = self.tree.item(child, "values")
            # Set status to "Checking..."
            self.tree.item(child, values=(server, sensor, ip, "Checking..."), tags=("Checking",))
            self.root.update_idletasks()  # Update UI

            # Perform ping test
            ping_status = self.ping_ip(ip)
            if ping_status == "Active":
                status = f"Ping: {ping_status}"

                #update progress bar
                self.tree.item(child, values=(server, sensor, ip, status), tags=(ping_status,))


            else:
                # Perform trace route
                trace_status = self.trace_route(ip)
                status = f"Ping: {ping_status} | Trace route: {trace_status}"
                # update progress bar
                self.tree.item(child, values=(server, sensor, ip, status), tags=(ping_status,))

            self.progress_bar["value"] += 1
            self.root.update_idletasks()
            # Combine results

            # print(trace_status)
            # self.tree.item(child, values=(server, sensor, ip, status), tags=(ping_status,))
            #
            # # Update progress bar
            # self.progress_bar["value"] += 1
            # self.root.update_idletasks()

        messagebox.showinfo("Info", "IP status check completed.")
    def ping_ip(self, ip):
        try:
            result = subprocess.run(
                ["ping", "-c", "1", ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # if result.returncode == 0:
            #     return "Active"
            # else:
            #     return "Inactive"
            ping_status = ["Active","Inactive"]
            return random.choice(ping_status)
        except Exception as e:
            print(f"Error pinging IP {ip}: {str(e)}")
            return "Error"

    def on_right_click(self, event):
        # Get the item at the cursor's position
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            # Select the item
            self.tree.selection_set(selected_item)
            # Show the context menu at the cursor's position
            self.context_menu.post(event.x_root, event.y_root)

    def check_again(self):
        # Get the selected item from the treeview
        selected_item = self.tree.selection()[0]
        server, sensor, ip, _ = self.tree.item(selected_item, "values")
        # Set status to "Checking..."
        self.tree.item(selected_item, values=(server, sensor, ip, "Checking..."), tags=("Checking",))
        self.root.update_idletasks()  # Update UI

        status = self.ping_ip(ip)
        self.tree.item(selected_item, values=(server, sensor, ip, status), tags=(status,))

    def trace_route(self, ip):
        try:
            # Execute the tracert command with a maximum of 10 hops
            result = subprocess.run(
                ["tracert", "-h", "10", ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                return "Success"  # Return the output of the tracert command

            else:
                return "Failed"

        except Exception as e:
            print(f"Error tracing route to IP {ip}: {str(e)}")
            return "Error"

    def click_tracert(self):
        # Get the selected item from the treeview
        selected_item = self.tree.selection()[0]
        server, sensor, ip, _ = self.tree.item(selected_item, "values")
        # Set status to "Checking..."
        self.tree.item(selected_item, values=(server, sensor, ip, "Checking..."), tags=("Checking",))
        self.root.update_idletasks()  # Update UI

        status = self.trace_route(ip)
        #self.tree.item(selected_item, values=(server, sensor, ip, status), tags=(status,))
        print(status)

def main():
   root = tk.Tk()
   app = ServerStatusChecker(root)
   root.mainloop()


   
if __name__ == "__main__":
    main()
