import concurrent.futures
import socket
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk  # Import ttk for combobox
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def is_valid_url(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.netloc)


def check_link(url, timeout):
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code >= 400:
            return url, response.status_code
        return None
    except (requests.exceptions.RequestException, socket.timeout):
        return url, "Timeout or Connection Error"
    except Exception as e:
        return url, str(e)


def check_dead_links():
    global dead_links
    url_or_ip = url_entry.get()
    max_threads = max_threads_combobox.get()
    timeout = timeout_combobox.get()

    if max_threads == "Customize":
        max_threads = int(custom_max_threads_entry.get())
    else:
        max_threads = int(max_threads)

    if timeout == "Customize":
        timeout = int(custom_timeout_entry.get())
    else:
        timeout = int(timeout)

    if not is_valid_url(url_or_ip):
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, "Invalid URL or IP address\n")
        log_text.config(state=tk.DISABLED)
        return

    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    log_text.insert(tk.END, f"Getting links from {url_or_ip}...\n")
    log_text.config(state=tk.DISABLED)
    log_text.update_idletasks()

    try:
        response = requests.get(url_or_ip, timeout=timeout)
        soup = BeautifulSoup(response.text, "html.parser")
        links = [link.get("href") for link in soup.find_all("a")]
    except Exception as e:
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, f"Error retrieving links: {str(e)}\n")
        log_text.config(state=tk.DISABLED)
        log_text.update_idletasks()
        return

    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, f"Found {len(links)} links.\n")
    log_text.config(state=tk.DISABLED)
    log_text.update_idletasks()

    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, "Checking links...\n")
    log_text.config(state=tk.DISABLED)
    log_text.update_idletasks()

    dead_links = []
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(check_link, link, timeout) for link in links]

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            if result is not None:
                dead_links.append(result)

            progress = i / len(links) * 100
            elapsed_time = time.time() - start_time
            if i > 0:
                time_remaining = (elapsed_time / i) * (len(links) - i)
            else:
                time_remaining = 0

            progress_bar['value'] = progress
            progress_label.config(text=f"Progress: {progress:.2f}%")
            time_label.config(text=f"Time Remaining: {int(time_remaining)} seconds")
            root.update_idletasks()

    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, f"Found {len(dead_links)} dead links.\n")
    log_text.config(state=tk.DISABLED)
    log_text.update_idletasks()

    if len(dead_links) > 0:
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, "Dead links found.\n")
        log_text.config(state=tk.DISABLED)
        log_text.update_idletasks()
    else:
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, "No dead links found.\n")
        log_text.config(state=tk.DISABLED)
        log_text.update_idletasks()


def view_results():
    global dead_links
    if not dead_links:
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, "No dead links to view.\n")
        log_text.config(state=tk.DISABLED)
        return

    result_text = "\n".join([f"{url} (Status Code: {status_code})" for url, status_code in dead_links])

    result_window = tk.Toplevel(root)
    result_window.title("Dead Links")

    result_text_widget = tk.Text(result_window, height=10, width=50)
    result_text_widget.pack()
    result_text_widget.insert(tk.END, result_text)
    result_text_widget.config(state=tk.DISABLED)

    result_window.mainloop()


def enable_custom_threads(event):
    selected_value = max_threads_combobox.get()
    if selected_value == "Customize":
        custom_max_threads_entry.config(state=tk.NORMAL)
    else:
        custom_max_threads_entry.config(state=tk.DISABLED)


def enable_custom_timeout(event):
    selected_value = timeout_combobox.get()
    if selected_value == "Customize":
        custom_timeout_entry.config(state=tk.NORMAL)
    else:
        custom_timeout_entry.config(state=tk.DISABLED)


def save_results():
    global dead_links
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "w") as f:
            for url, status_code in dead_links:
                f.write(f"{url} (Status Code: {status_code})\n")
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, f"Results saved as {file_path}\n")
        log_text.config(state=tk.DISABLED)
        log_text.update_idletasks()


root = tk.Tk()
root.title("Website Dead Link Checker By Erick Wilfred 2023")

url_label = tk.Label(root, text="Enter URL or IP:")
url_label.pack()

url_entry = tk.Entry(root, width=40)
url_entry.pack()

max_threads_label = tk.Label(root, text="Max Threads:")
max_threads_label.pack()

max_threads_values = ["1", "2", "4", "8", "16", "Customize"]
max_threads_combobox = ttk.Combobox(root, values=max_threads_values)
max_threads_combobox.set("1")
max_threads_combobox.pack()
max_threads_combobox.bind("<<ComboboxSelected>>", enable_custom_threads)

custom_max_threads_label = tk.Label(root, text="Customize Max Threads:")
custom_max_threads_label.pack()
custom_max_threads_entry = tk.Entry(root, width=10, state=tk.DISABLED)
custom_max_threads_entry.pack()

timeout_label = tk.Label(root, text="Timeout (seconds):")
timeout_label.pack()

timeout_values = ["5", "10", "30", "60", "120", "Customize"]
timeout_combobox = ttk.Combobox(root, values=timeout_values)
timeout_combobox.set("5")
timeout_combobox.pack()
timeout_combobox.bind("<<ComboboxSelected>>", enable_custom_timeout)

custom_timeout_label = tk.Label(root, text="Customize Timeout:")
custom_timeout_label.pack()

custom_timeout_entry = tk.Entry(root, width=10, state=tk.DISABLED)
custom_timeout_entry.pack()

progress_label = tk.Label(root, text="Progress: 0.00%")
progress_label.pack()

time_label = tk.Label(root, text="Time Remaining: Calculating...")
time_label.pack()

progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.pack()

log_text = tk.Text(root, height=10, width=50)
log_text.pack()
log_text.config(state=tk.DISABLED)

check_button = tk.Button(root, text="Check Website Dead Links", command=check_dead_links)
check_button.pack()

view_results_button = tk.Button(root, text="View Results", command=view_results)
view_results_button.pack()

save_button = tk.Button(root, text="Save Results", command=save_results)
save_button.pack()

dead_links = []

root.mainloop()
