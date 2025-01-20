import gpiod
import time
import tkinter as tk
from tkinter import messagebox, Button
import qrcode
import threading
import base64
import requests
from PIL import Image, ImageTk, ImageDraw, ImageOps 
import mysql.connector
from io import BytesIO
import re
import subprocess
from tkinter import ttk
import sys
from gif import AnimatedGIF
from modules.hx711.JoyIT_hx711py.HX711_PY import HX711


COIN_PIN = 17
INHIBIT_PIN = 23
BILL_PIN = 18

# Initialize GPIO chip and lines
chip = gpiod.Chip('gpiochip0')
coin_line = chip.get_line(COIN_PIN)
bill_line = chip.get_line(BILL_PIN)

coin_line.request(consumer='coin_slot', type=gpiod.LINE_REQ_DIR_IN, default_val=0)
bill_line.request(consumer='bill_acceptor', type=gpiod.LINE_REQ_DIR_IN, default_val=0)


def fetch_data_and_display():
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host="localhost",        # Replace with your MySQL host
            user="root",               # Replace with your MySQL username
            password="password",       # Replace with your MySQL password
            database="RVM"             # Replace with your MySQL database name
        )

        cursor = connection.cursor()
        cursor.execute("SELECT variety,price FROM rice")  # Query to fetch rice names

        # Fetch all rows of data
        rice_names = cursor.fetchall()

        # Update the buttons based on the available data
        if rice_names:
            # Extracting rice names from the fetched rows (assuming first column is rice_name)
            variety1 = rice_names[0][0] if len(rice_names) > 0 else "Not Available"
            variety2 = rice_names[1][0] if len(rice_names) > 1 else "Not Available"
            variety3 = rice_names[2][0] if len(rice_names) > 2 else "Not Available"

            klg1 = rice_names[0][1] if len(rice_names) > 0 else "N/A"
            klg2 = rice_names[1][1] if len(rice_names) > 1 else "N/A"
            klg3 = rice_names[2][1] if len(rice_names) > 2 else "N/A"

            # Update the button texts
            button1.config(text=variety1)
            button2.config(text=variety2)
            button3.config(text=variety3)

            label1.config(text=f"{klg1} Kg")
            label2.config(text=f"{klg2} Kg")
            label3.config(text=f"{klg3} Kg")

        else:
            messagebox.showinfo("No Data", "No rice names found in the database.")

    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", f"Error fetching data: {error}")
    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()


def on_button_click(value):
    # Get the current maximum price
    try:
        # Extract the first number from label_display and multiply by 10 to get max price
        max_price = float(label_display.cget("text").split()[0]) * 5  # 10 kg max
    except (ValueError, IndexError):
        max_price = 0  # Default to 0 if the label text is not valid

    if price_var.get() == "0":
        price_var.set("")
        current_text = price_var.get()

    if value == 'C':
        # Clear the textbox
        price_var.set("0")  
        feedback_label.config(text="")  # Clear feedback label
        feedback_label.place_forget()  # Hide feedback label
    elif value == 'X':
        # Remove the last character from the textbox
        current_text = price_var.get()
        if len(current_text) > 1:
            # Remove the last character if more than one digit
            price_var.set(current_text[:-1])
        else:
            # If only one digit or empty, set to "0"
            price_var.set("0")
        feedback_label.config(text="")  # Clear feedback label
        feedback_label.place_forget()  # Hide feedback label
    elif value == "Max":
        # When "Max" is clicked, set the price to the maximum value
        if max_price > 0:
            price_var.set(f"{int(max_price)}")  # Set to max price without .00
            feedback_label.config(text="Max price set.")  # Feedback for max price set
            feedback_label.place(x=10, y=380)  # Adjust position of feedback label
        else:
            feedback_label.config(text="Invalid max price.")  # Feedback for invalid max price
            feedback_label.place(x=10, y=380)  # Adjust position of feedback label
    else:
        # Handle numerical button inputs
        current_text = price_var.get()
        new_price = current_text + value  # Form the new price string

        # Validate against maximum price
        if float(new_price) > max_price:
            # Set to max price without .00
            price_var.set(f"{int(max_price)}")  # Convert max price to int to remove .00
            feedback_label.config(text="Price exceeds maximum limit. Only 5kg allowed.")  # Update feedback label
            feedback_label.place(x=10, y=460)  # Show feedback label at the desired position
        else:
            price_var.set(new_price)  # Update to the new price
            feedback_label.config(text="")  # Clear feedback if within limits
            feedback_label.place_forget()  # Hide feedback label if no message

        # Update the price variable globally
        global price
        try:
            price = float(price_var.get())  # Convert to float for price
        except ValueError:
            price = 0  # Default price to 0 in case of error




def open_home_window(button_number, button_text, label_text,main_window):
    main_window.withdraw()
    new_window = tk.Toplevel(root)
    new_window.configure(bg="#ffffff")
    set_fullscreen(new_window)
    new_window.wm_attributes("-type", "override")

    global selected_servo
    selected_servo = button_number

    global price_var, gcash_var, cash_var
    price_var = tk.StringVar(value="0")

    gcash_var = tk.BooleanVar()
    cash_var = tk.BooleanVar()
  
    def set_max_price(event=None):
        try:
            # Extract the price per kilogram from label_display (assuming 'XX klg' format)
            price_per_kg = float(label_display.cget("text").split()[0])  # Gets the price part before "klg"
            max_price = price_per_kg * 5  # Max is 10 kg

            # Convert to integer if the price is a whole number
            if max_price.is_integer():
                price_var.set(f"{int(max_price)}")  # Set as integer to remove .00
            else:
                price_var.set(f"{max_price}")  # Keep decimal if it's not a whole number
        except ValueError:
            price_var.set("0")  # Default to 0 in case of an error

    # Create a frame to hold the main content
    main_frame = tk.Frame(new_window, bg="#ffffff")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create a frame for the price textbox
    price_frame = tk.Frame(main_frame, bg="#ffffff")
    price_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=(20, 0))

    # Create a frame inside price_frame to hold the label and textbox
    price_content_frame = tk.Frame(price_frame, bg="#ffffff")
    price_content_frame.pack(side=tk.TOP, fill=tk.Y, anchor='w')  # Anchor to the left

    global rice_display
    rice_display = tk.Label(price_content_frame, text=button_text, font=("Arial", 98), bg="#ffffff", fg="black")
    rice_display.pack(pady=(0), padx=(20))

    global label_display
    label_display = tk.Label(price_content_frame, text=label_text, font=("Arial", 35), bg="#ffffff", fg="black")
    label_display.pack(pady=(0, 70), padx=(20))

    # Define the font for the header label
    header_font = ("Arial", 35, "bold")

    # Create a label for the price
    vcmd = (price_content_frame.register(validate_input), '%S')
    price_label = tk.Label(price_content_frame, text="Price", font=header_font, fg="black", bg="#ffffff")
    price_label.pack( padx=15,pady=0, anchor="w")

    # Frame to hold the price entry and "Max" label
    price_entry_frame = tk.Frame(price_content_frame, bg="#ffffff")
    price_entry_frame.pack(side=tk.TOP, pady=(20, 0), fill=tk.X)

    # Create the price textbox
    price_entry = tk.Entry(price_entry_frame, textvariable=price_var, font=("Arial", 58), justify="left", width=27)
    price_entry.pack(side=tk.LEFT, padx=10, expand=True)
    price_entry.bind("<FocusIn>", clear_default)

    # Create a label for feedback
    global feedback_label
    feedback_label = tk.Label(price_content_frame, text="", fg="red", bg="#ffffff")  # Red text for feedback
    feedback_label.place(relx=0, rely=1, anchor="sw")  # Adjust x and y for positioning     
    # Create the "Max" label
    # max_label = tk.Label(price_entry_frame, text="Max", font=("Arial", 18), bg="white", fg="black")
    #max_label.place(relx=1, rely=0.5, anchor="e", x=-10)  # Position it at the bottom-right corner inside the entry frame

    # Functionality for setting max price on clicking the label
    #max_label.bind("<Button-1>", set_max_price)

    # Create a label for the payment method
    payment_label = tk.Label(price_content_frame, text="Payment Method", bd=10, font=header_font, fg="black", bg="#ffffff")
    payment_label.pack( padx=10, pady=(60, 0), anchor="w")

    from tkinter import PhotoImage

    # Create a frame for the checkboxes under the price textbox
    checkbox_frame = tk.Frame(price_frame, background="gray", bd=1)
    checkbox_frame.pack(side=tk.TOP, pady=12)

    # Load the custom images
    unchecked_image = PhotoImage(file="/home/heartryan/Downloads/oval.png")  # Your unchecked image file
    checked_image = PhotoImage(file="/home/heartryan/Downloads/check.png")  # Your checked image file

    def gcash_checked():
        cash_var.set(False)
        gcash_var.set(True)
        gcash_checkbox.config(image=checked_image)
        cash_checkbox.config(image=unchecked_image)

    def cash_checked():
        gcash_var.set(False)
        cash_var.set(True)
        cash_checkbox.config(image=checked_image)
        gcash_checkbox.config(image=unchecked_image)

    # Create checkboxes with custom images and hide the default checkbox box
    gcash_checkbox = tk.Checkbutton(checkbox_frame, text="Gcash", variable=gcash_var, font=("Arial", 40), image=unchecked_image,
                                    selectimage=checked_image, compound="left", padx=138, pady=10, command=gcash_checked, indicatoron=False)
    cash_checkbox = tk.Checkbutton(checkbox_frame, text="Cash", variable=cash_var, font=("Arial", 40), image=unchecked_image,
                                selectimage=checked_image, compound="left", padx=138, pady=10, command=cash_checked, indicatoron=False)

    gcash_checkbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0), pady=0)
    cash_checkbox.pack(side=tk.LEFT, fill=tk.Y, padx=(1, 0), pady=0)

    # Create a frame to hold the buttons
    button_frame = tk.Frame(main_frame,bg="#ffffff")
    button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=(155, 0))

    # Define button properties
    button_width = 10
    button_height = 3
    button_font = ("Arial", 23)

    # List of buttons to create
    buttons = [
        ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
        ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
        ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
        ('0', 3, 1), ('C', 3, 0), ('X', 3, 2)
    ]

    # Create and place the buttons on the grid
    for (text, row, col) in buttons:
        button = tk.Button(button_frame, text=text, width=button_width, height=button_height, font=button_font, 
                           bg="#508D4E", fg="black", command=lambda t=text: on_button_click(t))
        button.grid(row=row, column=col, padx=10, pady=10)

    # Create a frame for the action buttons (Cancel and Pay)
    button_frame_bottom = tk.Frame(new_window,bg="#ffffff")
    button_frame_bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(0,60), padx=20)

    # Add buttons to proceed and cancel
    Cancel_button = tk.Button(button_frame_bottom, text="Cancel", width=36, height=3, bg="lightgray", fg="black", font=("Arial", 35),bd=1, relief="solid", command=lambda: [main_window.deiconify(), new_window.destroy()])
    Cancel_button.pack(side=tk.LEFT, padx=(10,2))
    Cancel_button.bind("<Button-1>", lambda e:  [main_window.deiconify(), new_window.destroy()])

    proceed_button = tk.Button(button_frame_bottom, text="Pay", width=40, height=3, bg="#508D4E", fg="black", font=("Arial", 35), command=lambda: [validate_and_proceed(cash_var.get(), new_window,main_window, rice_display.cget("text"),label_display.cget("text"))])
    proceed_button.pack(side=tk.RIGHT, padx=(2,10))

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    return label_display

def on_enter(e):
    e.widget['background'] = 'white'  # Change to desired hover color
    e.widget['foreground'] = 'black'    # Optionally change the text color

def on_leave(e):
    e.widget['background'] = '#508D4E'  # Reset to the original color
    e.widget['foreground'] = 'white'    # Optionally reset the text color



import tkinter as tk

def show_custom_messagebox(title, message):
    # Create a new top-level window for the custom messagebox
    messagebox_window = tk.Toplevel(root)
    messagebox_window.wm_attributes("-type", "override")

    # Set size of the messagebox
    window_width = 800
    window_height = 400

    # Get screen width and height
    screen_width = messagebox_window.winfo_screenwidth()
    screen_height = messagebox_window.winfo_screenheight()

    # Calculate the x and y coordinates for centering the window
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    # Set the geometry of the messagebox (width x height + x offset + y offset)
    messagebox_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create a frame inside the window for padding
    frame = tk.Frame(messagebox_window, padx=20, pady=20)
    frame.pack(expand=True)

    # Create a label for the message
    label = tk.Label(frame, text=message, font=("Arial", 18), wraplength=350)
    label.pack(pady=10)

    # Create an OK button to close the custom messagebox
    ok_button = tk.Button(frame, text="OK", width=25, height=3, font=("Arial", 14), bg="#508D4E", fg="white", command=messagebox_window.destroy)
    ok_button.pack(pady=40)

    # Automatically close the messagebox after 2 seconds (2000 milliseconds)
    messagebox_window.after(2000, messagebox_window.destroy)

    # Function to close the messagebox when the main window is clicked
    def close_messagebox(event):
        messagebox_window.destroy()

    # Bind the click event to the root window
    root.bind("<Button-1>", close_messagebox)

    # Unbind the click event when the messagebox is closed
    messagebox_window.protocol("WM_DELETE_WINDOW", lambda: (messagebox_window.destroy(), root.unbind("<Button-1>")))


def format_price():
    try:
        # Check if the input is empty and set it to "0"
        if price_var.get().strip() == "":
            price_var.set("0")
        else:
            # Replace commas with empty strings before converting to float
            value = float(price_var.get().replace(',', ''))
            # Convert to int if it's a whole number, otherwise keep as is
            formatted_value = f"{int(value)}" if value.is_integer() else f"{value}"
            price_var.set(formatted_value)
    except ValueError:
        price_var.set("0")  # Set to "0" if conversion fails

# Function to clear "0" when textbox is clicked
def clear_default(event):
    if price_var.get() == "0":
        price_var.set("")

# Function to validate input (only numbers and commas allowed)
def validate_input(char):
    # Allow only digits and commas
    return char.isdigit() or char == ","
    
def validate_and_proceed(is_cash, new_window,main_window, label_display, rice_display):
    format_price()
    try:
        price = float(price_var.get())
    except ValueError:
        price = 0

    if price < 20:
        show_custom_messagebox("Invalid Price", "Please input a valid price of at least 20")
        return
    if not gcash_var.get() and not cash_var.get():
        show_custom_messagebox("Payment Method", "Please select a payment method")
        return
    if gcash_var.get():
        generate_gcash_qr(price, new_window)

        new_window.withdraw()
    if cash_var.get():
        proceed(is_cash,new_window,main_window,label_display,rice_display)

        new_window.withdraw()


# Initialize counts and price
pulse_count = 0
bill_pulse_count = 0
price = 0
total_amount = 0.00

coin_pulse_map = {1: 1.00, 5: 5.00, 10: 10.00, 20: 20.00}  # Pulses to coin value
bill_value_map = {
    2: 20.00,   # 20 PHP (2 pulses)
    3: 50.00,   # 50 PHP (3 pulses)
    5: 100.00,  # 100 PHP (4 pulses)
    10: 200.00,  # 200 PHP (5 pulses)
    25: 500.00,  # 500 PHP (6 pulses)
    50: 1000.00, # 1000 PHP (7 pulses)
    1: 10.00   # 10 PHP (10 pulses)
}

DEBOUNCE_TIME = 0.05  # Increased debounce time
POLLING_INTERVAL = 0.01  # Polling interval for fast response


def monitor_inputs(cash_window, label_display, main_window, new_window,rice_display):
    """Monitor coin and bill acceptor inputs and update the total amount."""
    global pulse_count, bill_pulse_count, total_amount, monitoring
    previous_coin_value = coin_line.get_value()
    previous_bill_value = bill_line.get_value()
    
    pulse_start_time = time.perf_counter()

    while monitoring:
        current_coin_value = coin_line.get_value()
        current_bill_value = bill_line.get_value()

        # Handle coin pulses
        if previous_coin_value == 1 and current_coin_value == 0:
            pulse_count += 1
            pulse_start_time = time.perf_counter()
            print(f"Coin Pulse Detected: {pulse_count}")

        # Handle bill pulses
        if previous_bill_value == 1 and current_bill_value == 0:
            bill_pulse_count += 1
            pulse_start_time = time.perf_counter()
            print(f"Bill Pulse Detected: {bill_pulse_count}")

        # Check for completed coin pulses
        if pulse_count > 0 and (time.perf_counter() - pulse_start_time) > DEBOUNCE_TIME:
            if pulse_count in coin_pulse_map:
                inserted_amount = coin_pulse_map[pulse_count]
                total_amount += inserted_amount
                disable_back_button()
                coin_count_label.config(text=f"Total Amount Inserted: {total_amount:.2f} PHP")
                print(f"Inserted coin value: {inserted_amount:.2f} PHP")
            pulse_count = 0  # Reset pulse count

        # Check for completed bill pulses
        if bill_pulse_count > 0 and (time.perf_counter() - pulse_start_time) > DEBOUNCE_TIME:
            if bill_pulse_count in bill_value_map:
                inserted_amount = bill_value_map[bill_pulse_count]
                total_amount += inserted_amount
                disable_back_button()
                coin_count_label.config(text=f"Total Amount Inserted: {total_amount:.2f} PHP")
                print(f"Inserted bill value: {inserted_amount:.2f} PHP")
            bill_pulse_count = 0  # Reset pulse count

        # Update previous values for the next loop iteration
        previous_coin_value = current_coin_value
        previous_bill_value = current_bill_value
        time.sleep(POLLING_INTERVAL)

        # Check if payment is sufficient
        check_payment(cash_window, label_display, main_window, new_window,rice_display)



def confirm_cancel(new_window, cash_window):
    # Create a new top-level window for the custom messagebox
    confirm_window = tk.Toplevel(root)
    confirm_window.wm_attributes("-type", "override")
    
    # Set size of the messagebox
    window_width = 1000
    window_height = 600         

    # Get screen width and height
    screen_width = confirm_window.winfo_screenwidth()
    screen_height = confirm_window.winfo_screenheight()

    # Calculate the x and y coordinates for centering the window
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    # Set the geometry of the messagebox (width x height + x offset + y offset)
    confirm_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    disable_back_button()

    # Message Label
    tk.Label(confirm_window, text="Are you sure you want to cancel?", font=("Arial", 24)).pack(pady=(100,0))

    button_frame = tk.Frame(confirm_window)
    button_frame.pack(side=tk.BOTTOM,pady=40)

    def on_confirm():
        global pulse_count, bill_pulse_count, total_amount, monitoring
        pulse_count = 0  # Reset pulse count
        bill_pulse_count = 0  # Reset bill pulse count
        total_amount = 0.00  # Reset total amount
        monitoring = False  # Stop the monitoring thread

        # Update the coin count label
        coin_count_label.config(text="Total Amount Inserted: 0.00 PHP")

        cash_window.destroy()
        confirm_window.destroy() 
        new_window.deiconify()  

    def cancel_btn():
        Enable_button()
        confirm_window.destroy()

    # Confirm and Cancel buttons
    confirm_button = tk.Button(button_frame, text="Yes", font=("Arial", 18), width=30, bg="#508D4E", height=3,command=on_confirm)
    confirm_button.pack(side=tk.LEFT, padx=10,pady=10, anchor="sw")
    cancel_button = tk.Button(button_frame, text="No", width=30, height=3, bg="lightgrey", fg="black", font=("Arial", 18), bd=1, relief="solid",command=cancel_btn)
    cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)
   
def Enable_button():
    global Back_button
    if Back_button:
        Back_button.config(state=tk.NORMAL)  # Disable the Back button

def disable_back_button():
    global Back_button
    if Back_button:
        Back_button.config(state=tk.DISABLED)  # Disable the Back button
def blink_label1(label1):
    current_color = label1.cget("fg")
    next_color = "#000000" if current_color == "green" else "green"
    label1.config(fg=next_color)
    label1.after(500, blink_label1, label1)
def proceed(is_cash, new_window, main_window, rice_display, label_display):
    global pulse_count, bill_pulse_count, progress_bar, percentage_label  # Declare progress bar and percentage label as global

    if is_cash:
        root.withdraw()
        new_window.withdraw()

        # Create the cash window
        cash_window = tk.Toplevel(root)
        cash_window.configure(bg="#508D4E")  # Dark background
        set_fullscreen(cash_window)
        cash_window.wm_attributes("-type", "override")

        # Create the Back button to trigger the confirmation dialog
        global Back_button
        Back_button = tk.Button(
            cash_window, text="Cancel", width=14, height=2, bg="lightgrey", fg="black",
            font=("Arial", 24), bd=1, relief="solid",
            command=lambda: confirm_cancel(new_window, cash_window)  # Trigger confirmation
        )
        Back_button.pack(side=tk.TOP, anchor='nw', padx=20, pady=20)    

                # Create a main content frame with padding and solid borders
        center_frame1 = tk.Frame(cash_window, bg="#508D4E")  # Outer background
        center_frame1.pack(expand=True, fill=tk.BOTH, padx=20, pady=0)
        center_frame = tk.Frame(center_frame1, bg="white", bd=1, relief="solid")  # Inner white frame with border
        center_frame.pack(expand=True, fill=tk.BOTH, padx=400, pady=(80, 150))

        # Header section with bold text and underline
        header_label = tk.Label(
            center_frame, 
            text="Insert Exact Amount", 
            font=("Arial", 26, "bold"), 
            bg="white", 
            fg="#4B3D8E"  # Use a modern color for the header
        )
        header_label.pack(pady=(30, 10))

        # Sub-header for no-change notice
        subheader_label = tk.Label(
            center_frame, 
            text="Change is not available. Thank you for understanding.", 
            font=("Arial", 14, "italic"), 
            bg="white", 
            fg="gray"
        )
        subheader_label.pack(pady=(5, 20))

        # Add a horizontal separator
        separator_line = tk.Frame(center_frame, height=2, width=500, bg="#E0E0E0")
        separator_line.pack(pady=(5, 20))

        # Rice label for product name with modern styling
        rice_label = tk.Label(
            center_frame, 
            text=rice_display, 
            font=("Arial", 36, "bold"), 
            bg="white", 
            fg="#4B3D8E"
        )
        rice_label.pack(pady=(10, 20))

        # Price display with emphasized design
        price_label_frame = tk.Frame(center_frame, bg="white", bd=2, relief="ridge")
        price_label_frame.pack(pady=(10, 20), padx=20)
        price_label = tk.Label(
            price_label_frame, 
            text=f" Price: {price_var.get()} ", 
            font=("Arial", 22, "bold"), 
            bg="white", 
            fg="#000000"  # Green for monetary emphasis
        )
        price_label.pack(padx=20, pady=10)

        # Total inserted amount display
        global coin_count_label
        coin_count_label = tk.Label(
            center_frame, 
            text="Total Amount Inserted: ₱0.00", 
            font=("Arial", 20), 
            bg="white", 
            fg="#000000"  # Modern teal for progress tracking
        )
        coin_count_label.pack(pady=(20, 10))

        global processing_label
        processing_label = tk.Label(center_frame, text="Processing...", font=("Arial", 24), bg="white", fg="#4B3D8E")
        processing_label.pack_forget()  # Hide initially

        # Instruction label with blinking effect
        global blinkn_label
        blinkn_label = tk.Label(
            center_frame, 
            text="Please insert coins or bills to proceed.", 
            font=("Arial", 20, "bold"), 
            bg="white", 
            fg="#000000"  # Red for urgency
        )
        blinkn_label.pack(pady=(20, 10))
        blink_label1(blinkn_label)

        # Progress bar container with percentage display
        global progress_bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor="#e0e0e0",
            background="#4B3D8E",
            thickness=70,
        )

        progress_bar = ttk.Progressbar(
            center_frame,
            style="green.Horizontal.TProgressbar",
            length=700,
            mode="determinate",
        )
        progress_bar.pack(pady=(30, 10))
        progress_bar.pack_forget()

        # Percentage label below the progress bar
        percentage_label = tk.Label(center_frame, text="0%", font=("Arial", 22), bg="white", fg="#000000")
        percentage_label.pack_forget()  # Hide initially

        # Initialize monitoring for cash input
        global monitoring
        monitoring = True
        threading.Thread(target=monitor_inputs, args=(cash_window, label_display, main_window, new_window, rice_display), daemon=True).start()

        # Start dispensing rice
        threading.Thread(target=dispense_rice, args=(label_display, price_var.get(), new_window, cash_window, rice_display), daemon=True).start()   

"""
def proceed(is_cash, new_window, main_window, rice_display, label_display):
    global pulse_count, bill_pulse_count, progress_bar, percentage_label  # Declare progress bar and percentage label as global

    if is_cash:
        root.withdraw()
        new_window.withdraw()

        # Create the cash window
        cash_window = tk.Toplevel(root)
        cash_window.configure(bg="#363062")  # Dark background
        set_fullscreen(cash_window)
        cash_window.wm_attributes("-type", "override")

        # Create the Back button to trigger the confirmation dialog
        global Back_button
        Back_button = tk.Button(
            cash_window, text="Cancel", width=14, height=2, bg="lightgrey", fg="black",
            font=("Arial", 24), bd=1, relief="solid",
            command=lambda: confirm_cancel(new_window, cash_window)  # Trigger confirmation
        )
        Back_button.pack(side=tk.TOP, anchor='nw', padx=20, pady=20)    

        # Create a main content frame with padding
        center_frame1 = tk.Frame(cash_window, bg="#4B3D8E")  # Lighter purple background
        center_frame1.pack(expand=True, fill=tk.BOTH, padx=20, pady=0)
        center_frame = tk.Frame(center_frame1, bg="white", bd=1, relief="solid")  # Lighter purple background
        center_frame.pack(expand=True, fill=tk.BOTH, padx=500, pady=(100, 200))

        no_change = tk.Label(center_frame, text="Please insert the exact amount. Change is not available.", font=("Arial", 18, 'bold'), bg="white", fg="black")
        no_change.pack(pady=(30, 30))

        # Rice label
        rice_label = tk.Label(center_frame, text=rice_display, font=("Arial", 48, 'bold'), bg="white", fg="black")
        rice_label.pack(pady=(30, 10))

        # Price label
        price_label = tk.Label(center_frame, text=f"Price: {price_var.get()}", font=("Arial", 24), bg="white", fg="black")
        price_label.pack(pady=(20, 10))

        global coin_count_label
        coin_count_label = tk.Label(center_frame, text="Total Amount Inserted: 0.00", font=("Arial", 24), bg="white", fg="black")
        coin_count_label.pack(pady=(20, 10))

        # Processing label (Initially hidden)
        global processing_label
        processing_label = tk.Label(center_frame, text="Processing...", font=("Arial", 24), bg="white", fg="green")
        processing_label.pack_forget()  # Hide initially

        # Blinking label
        global blinkn_label
        blinkn_label = tk.Label(center_frame, text="Please Insert Coin or Bill.", font=("Arial", 22), bg="white", fg="red")
        blinkn_label.pack(pady=(20, 10))

        blink_label1(blinkn_label)

        # Progress bar (Initially hidden)
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor="#e0e0e0",
            background="#4CAF50",
            thickness=70,
        )

        progress_bar = ttk.Progressbar(
            center_frame,
            style="green.Horizontal.TProgressbar",
            length=700,
            mode="determinate",
        )
        # Do not pack the progress bar initially
        progress_bar.pack_forget()

        # Percentage label below the progress bar
        percentage_label = tk.Label(center_frame, text="0%", font=("Arial", 22), bg="white", fg="black")
        percentage_label.pack_forget()  # Hide initially

        # Initialize monitoring for cash input
        global monitoring
        monitoring = True
        threading.Thread(target=monitor_inputs, args=(cash_window, label_display, main_window, new_window, rice_display), daemon=True).start()

        # Start dispensing rice
        threading.Thread(target=dispense_rice, args=(label_display, price_var.get(), new_window, cash_window, rice_display), daemon=True).start() """

def cleanup1():
    global monitoring
    monitoring = False
    try:
        coin_line.release()
        bill_line.release()
    except Exception as e:
        print(f"Error during GPIO cleanup: {e}")

hx = HX711(dout=16, pd_sck=5)
hx.set_offset(8504030.4)  # Calibrated offset
hx.set_scale(89.6353448)  # Calibrated scale

FIXED_TARE_WEIGHT = 100  # Fixed tare weight in grams
WEIGHT_TOLERANCE = 100

import requests
import time

esp8266_ip = "http://192.168.123.41"  # Replace with the ESP8266 IP

def rotate_servo(angle, servo_id):
    """Send a command to the ESP8266 to rotate a servo."""
    if servo_id not in [1, 2, 3, 4]:
        print("Invalid servo ID. Use 1, 2, 3, or 4.")
        return
    if angle not in [10, 30]:  # Restrict to open (80) and close (10)
        print("Invalid angle. Use 10 or 80.")
        return

    url = f"{esp8266_ip}/servo/{servo_id}?angle={angle}"
    try:
        response = requests.get(url, timeout=5)  # Add a timeout for requests
        if response.status_code == 200:
            print(f"Servo {servo_id} rotated to {angle} degrees.")
        else:
            print(f"Failed to rotate servo {servo_id}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with ESP8266: {e}")

import tkinter as tk

# Blinking label effect


import datetime
import random

def insert_transaction(transaction_id, date_time, rice_type, price_per_unit, weight_dispensed, total_amount, payment_method, status):
    try:
        # Establish database connection
        connection = mysql.connector.connect(
            host="localhost",        # Replace with your MySQL host
            user="root",               # Replace with your MySQL username
            password="password",       # Replace with your MySQL password
            database="RVM" 
        )
        cursor = connection.cursor()

        # Insert query
        query = """
        INSERT INTO transactions1 
        (transaction_id, date_time, rice_type, price_per_unit, weight_dispensed, total_amount, payment_method, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (transaction_id, date_time, rice_type, price_per_unit, weight_dispensed, total_amount, payment_method, status)

        cursor.execute(query, values)
        connection.commit()
        print(f"Transaction {transaction_id} inserted successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


from tkinter import ttk
def dispense_rice(label_display, price, new_window, cash_window, rice_display):
    """Dispense rice based on the price and selected servo, and update the progress bar."""

    def rotate_and_dispense():
        try:
            match = re.search(r'(\d+\.?\d*)\s*(?:klg|kg|per\s*kg)', label_display, re.IGNORECASE)
            if not match:
                raise ValueError("Invalid label display format")

            price_per_kg = float(match.group(1))
            weight_to_dispense = (price / price_per_kg) * 1000  # Convert to grams
            total_weight_to_dispense = weight_to_dispense + FIXED_TARE_WEIGHT  # Include tare weight
            progress_bar["maximum"] = weight_to_dispense  # Set max for progress bar

            cash_window.after(0, lambda: processing_label.pack(pady=30))
            cash_window.after(0, lambda: progress_bar.pack(pady=15))
            cash_window.after(0, lambda: percentage_label.pack(pady=(10, 0)))  # Show percentage label
            blinkn_label.pack_forget()  # Hide blinking label

            # Start dispensing by rotating the servo
            print(f"Starting rice dispensing for Servo {selected_servo}.")
            rotate_servo(30, selected_servo)  # Open servo
            initial_weight = hx.get_grams(10)  # Initial reading from load cell
            current_weight = 0.0

            print(f"Initial weight: {initial_weight:.2f} grams")
            MAX_VALID_WEIGHT = 7100.0

            # Monitor the current weight
            while current_weight < total_weight_to_dispense:
                total_weight = hx.get_grams(10) + FIXED_TARE_WEIGHT
                raw_weight = total_weight - initial_weight

                if raw_weight < 0:
                    print("Invalid weight reading, retrying...")
                    time.sleep(0.1)
                    continue 

                if total_weight > MAX_VALID_WEIGHT:
                    print(f"Erratic reading: {total_weight:.2f} grams. Ignoring...")
                    time.sleep(0.1)  # Delay before rechecking
                    continue  # Skip this invalid reading

                # Handle valid weight readings
                if raw_weight >= 0:
                    current_weight = raw_weight
                    print(f"Current weight dispensed: {current_weight:.2f} grams")

                # Calculate and handle valid percentage
                percentage = (current_weight / total_weight_to_dispense) * 100
                if percentage > 100:  # Ensure percentage does not exceed 100
                    percentage = 100

                progress_bar["value"] = current_weight
                percentage_label.config(text=f"{percentage:.0f}%")  # Update percentage label
                processing_label.config(text="Processing...")
                cash_window.update_idletasks()  # Refresh UI

                if current_weight >= total_weight_to_dispense:
                    print("Target weight reached. Closing the servo.")
                    rotate_servo(10, selected_servo)  # Close servo
                    progress_bar["value"] = total_weight_to_dispense
                    percentage_label.config(text="100%")  # Ensure 100% is displayed
                    cash_window.update_idletasks()
                    rice_dispensed1(new_window, cash_window, total_weight_to_dispense, total_amount, label_display, rice_display)  # Use current_weight
                    break

                time.sleep(0.1)

        except Exception as e:
            print(f"Error during rice dispensing: {e}")
    threading.Thread(target=rotate_and_dispense, daemon=True).start()
    
def rice_dispensed1(new_window, cash_window, total_weight_to_dispense, total_amount, label_display, rice_display):
    dispensed_window1 = tk.Toplevel(root)
    dispensed_window1.wm_attributes("-type", "override")
    dispensed_window1.configure(bg="#f4f4f4")  # Soft background color

    # Define window size
    window_width = 500
    window_height = 700

    # Get screen width and height
    screen_width = dispensed_window1.winfo_screenwidth()
    screen_height = dispensed_window1.winfo_screenheight()

    # Calculate x and y coordinates for centering the window    
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    # Set the geometry of the window
    dispensed_window1.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create a frame for the receipt details
    receipt_frame = tk.Frame(dispensed_window1, bg="white", relief="solid", bd=2, padx=10, pady=10)
    receipt_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    # Receipt title
    receipt_title = tk.Label(receipt_frame, text="RICE VENDING MACHINE", font=("Courier New", 18, "bold"), bg="white", fg="black")
    receipt_title.pack(pady=(10, 5))

    # Divider line
    divider = tk.Label(receipt_frame, text="-" * 40, font=("Courier New", 12), bg="white", fg="black")
    divider.pack(pady=(5, 5))

    # Transaction ID
    transaction_id = f"TXN-{random.randint(100000, 999999)}"
    transaction_id_label = tk.Label(receipt_frame, text=f"Transaction ID: {transaction_id}", font=("Courier New", 12), bg="white", fg="black")
    transaction_id_label.pack(anchor="w", pady=(5, 0))

    # Date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datetime_label = tk.Label(receipt_frame, text=f"Date & Time: {current_time}", font=("Courier New", 12), bg="white", fg="black")
    datetime_label.pack(anchor="w", pady=(5, 10))

    # Divider line
    divider = tk.Label(receipt_frame, text="-" * 40, font=("Courier New", 12), bg="white", fg="black")
    divider.pack(pady=(5, 10))

    # Rice details
    rice_type_label = tk.Label(receipt_frame, text=f"Rice Type: {rice_display}", font=("Courier New", 12), bg="white", fg="black")
    rice_type_label.pack(anchor="w", pady=(5, 0))

    price_label = tk.Label(receipt_frame, text=f"Price per Unit: {label_display} PHP", font=("Courier New", 12), bg="white", fg="black")
    price_label.pack(anchor="w", pady=(5, 0))

    label_rice_calculate = total_weight_to_dispense - FIXED_TARE_WEIGHT
    rice_dispensed_label = tk.Label(receipt_frame, text=f"Quantity: {label_rice_calculate:.2f} grams", font=("Courier New", 12), bg="white", fg="black")
    rice_dispensed_label.pack(anchor="w", pady=(5, 0))

    total_amount_label = tk.Label(receipt_frame, text=f"Amount Paid: {total_amount:.2f} PHP", font=("Courier New", 12), bg="white", fg="black")
    total_amount_label.pack(anchor="w", pady=(5, 10))

    # Divider line
    divider = tk.Label(receipt_frame, text="-" * 40, font=("Courier New", 12), bg="white", fg="black")
    divider.pack(pady=(5, 10))

    # Thank you message
    confirmation_label = tk.Label(receipt_frame, text="THANK YOU!", font=("Courier New", 14, "bold"), bg="white", fg="green")
    confirmation_label.pack(pady=(10, 5))

    # Instructions for bag/container
    bag_label = tk.Label(receipt_frame, text="Please collect your rice.", font=("Courier New", 12), bg="white", fg="black")
    bag_label.pack(pady=(5, 10))

    insert_transaction(
        transaction_id=transaction_id,
        date_time=current_time,
        rice_type=rice_display,
        price_per_unit=label_display,
        weight_dispensed=label_rice_calculate,
        total_amount=total_amount,
        payment_method="Cash",  # Or "GCash", based on your implementation
        status="success"
    )
    monitor_bag_and_release(total_weight_to_dispense,new_window, cash_window)

import lgpio as GPIO
import time
from collections import deque

# Set GPIO pins
TRIG = 6 
ECHO = 12  

# Open the GPIO chip and set the GPIO direction
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

# Function to measure distance
def get_distance():
    # Set TRIG LOW
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(0.002)

    # Send 10us pulse to TRIG
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    GPIO.gpio_write(h, TRIG, 0)

    # Start recording the time when the wave is sent
    while GPIO.gpio_read(h, ECHO) == 0:
        pulse_start = time.time()

    # Record time of arrival
    while GPIO.gpio_read(h, ECHO) == 1:
        pulse_end = time.time()

    # Calculate the difference in times
    pulse_duration = pulse_end - pulse_start

    # Multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = pulse_duration * 17150
    return round(distance, 2)

# Function to monitor bag and release rice
def monitor_bag_and_release(total_weight_to_dispense, new_window, cash_window):
    """Check for a bag using an ultrasonic sensor and release rice when detected."""
    print("Waiting for bag detection...")
    bag_detected = False
    distance_readings = deque(maxlen=5)

    while not bag_detected:
        distance = get_distance()
        distance_readings.append(distance)
        average_distance = sum(distance_readings) / len(distance_readings)
        print(f"Average Distance: {average_distance:.2f} cm")

        if average_distance < 30: 
            print("Bag detected!")
            bag_detected = True
            open_servo_and_release_rice(total_weight_to_dispense)
        else:
            print("No bag detected. Waiting...")
            time.sleep(0.5)  # Check every 500ms

def open_servo_and_release_rice(total_weight_to_dispense):
    """
    Use the ultrasonic sensor to detect a bag/container and open Servo 4 for rice release.
    Close the servo temporarily when no bag is detected, and wait for the user to place the bag back to continue dispensing.
    """
    print("Monitoring for bag/container and dispensing rice...")
    distance_readings = deque(maxlen=5)  # Store the last 5 distance readings
    is_servo_open = False
    initial_weight = hx.get_grams(10)  # Take 10 readings for stability
    print(f"Initial weight (tare): {initial_weight:.2f} grams")
    total_weight_to_dispense1 = total_weight_to_dispense 

    while True:
        distance = get_distance()
        distance_readings.append(distance)
        average_distance = sum(distance_readings) / len(distance_readings)
        print(f"Average Distance: {average_distance:.2f} cm")

        if average_distance < 40 and not is_servo_open:
            print("Bag detected! Opening Servo 4.")
            rotate_servo(30, 3)  # Replace with servo control
            is_servo_open = True
        # Monitor the current weight while the servo is open
        if is_servo_open:
            current_weight = hx.get_grams(10)  # Average over 10 readings
            weight_reduction = initial_weight - current_weight  # Calculate reduction
            MAX_VALID_WEIGHT = 7100.0

            # Check if the reading is within a valid range
            if current_weight > MAX_VALID_WEIGHT:
                print(f"Erratic reading detected: {current_weight:.2f} grams. Ignoring...")
                time.sleep(0.1)  # Delay before rechecking
                continue  # Skip this invalid reading

            # Handle valid weight reduction
            print(f"Weight reduction: {weight_reduction:.2f} grams")

            # Check if all rice is dispensed
            if weight_reduction >= total_weight_to_dispense1:
                print("Target weight dispensed. Closing the servo.")
                rotate_servo(10, 3)
                is_servo_open = False
                break

            if weight_reduction < 0:
                print("Invalid weight reading. Retrying...")
                time.sleep(0.1)
                continue

        time.sleep(0.1)

    # All rice dispensed
    print("Dispensing complete. Restarting system.")
    close_and_restart()

def cleanup_hx711(hx):
    """Cleanup HX711 GPIO resources."""
    try:
        hx.cleanup()
        print("HX711 resources cleaned up.")
    except Exception as e:
        print(f"Error during HX711 cleanup: {e}")

def global_gpio_cleanup():
    """Release all GPIO resources."""
    try:
        GPIO.gpiochip_close(h)  # Close the GPIO chip
        print("All GPIO resources released.")
    except Exception as e:
        print(f"Error during GPIO cleanup: {e}")

def close_all_windows():
    """Close all open windows, including the main root window."""
    for window in root.winfo_children():
        if isinstance(window, tk.Toplevel):  # Check if it's a Toplevel window
            print(f"Closing window: {window}")
            window.destroy()


def close_and_restart():
    """Close all windows and restart the program."""
    try:
        close_all_windows()  # Close all Tkinter windows
        cleanup_hx711(hx)  # Clean up HX711 resources
        global_gpio_cleanup()  # Release GPIO resources

        time.sleep(1)  # Allow resources to release
        print("Restarting the system...")
        subprocess.Popen([sys.executable, sys.argv[0]])  # Restart script
        sys.exit()
    except Exception as e:
        print(f"Error during restart: {e}")



def disable_dispense_button():
    global open_button
    if open_button:
        open_button.config(state=tk.DISABLED)

def check_payment(cash_window, label_display, main_window, new_window,rice_display):
    global total_amount, price

    if total_amount >= price:
        print("Payment successful!")
        cleanup1()  # Ensure GPIO resources are freed
        dispense_rice(label_display, price, new_window, cash_window, rice_display)

"""
import base64
import requests
import qrcode
from PIL import Image, ImageTk
import tkinter as tk
import time

XENDIT_SECRET_KEY = 'xnd_development_784ZEXK9AlW58ZU0G14xcX1riWoh9UbT1IMNu234woi3I9b7BPVZNpedKGoHkq'  # Replace with your Xendit secret key

def create_gcash_payment(price, description='GCash Payment', success_url='https://www.blackbox.ai/chat/KZxNPpV', fail_url='http://yourdomain.com/failed'):
    url = "https://api.xendit.co/ewallets"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{XENDIT_SECRET_KEY}:'.encode()).decode()}",
        "Content-Type": "application/json",
    }

    data = {
        "amount": int(price * 100),  # Convert to centavos
        "currency": "PHP",
        "ewallet_type": "GCASH",
        "callback_url": "https://webhook.site/5eebb675-6102-453a-a81c-de95fb08bc77",  # Replace with your webhook URL
        "redirect_url": success_url,
        "failure_redirect_url": fail_url,
        "reference_id": f"rice_vending_{int(time.time())}",  # Unique transaction ID
        "metadata": {
            "description": description,
        },
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    if response.status_code == 200:
        return response_data["actions"]["mobile_web_checkout_url"]
    else:
        print(f"Error creating GCash payment: {response_data}")
        return None

def generate_gcash_qr(price, new_window):   
    # Create GCash payment link
    payment_url = create_gcash_payment(price)

    if payment_url:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,       
        )
        qr.add_data(payment_url)
        qr.make(fit=True)

        # Create an image from the QR Code instance
        img = qr.make_image(fill="black", back_color="white")

        # Save the image or display it
        img_path = "gcash_payment_qr.png"
        img.save(img_path)

        # Open the QR code in a new window
        show_qr_window(img_path, new_window)
    else:
        print("Failed to create GCash payment.")

def show_qr_window(img_path, new_window):
    # Create a new top-level window
    new_window.withdraw()
    qr_window = tk.Toplevel(root)
    qr_window.configure(bg="#508D4E")
    set_fullscreen(qr_window)
    qr_window.wm_attributes("-type", "override")
    
    closebtn = tk.Button(qr_window, text="Cancel", width=14, height=2, bg="lightgrey", fg="black", font=("Arial", 24,),bd=1, relief="solid",
                            command=lambda: [new_window.deiconify(), qr_window.destroy()])
    closebtn.pack(side=tk.TOP, anchor='nw', padx=20, pady=20)

    # Load the saved QR image
    qr_image = Image.open(img_path)
    qr_photo = ImageTk.PhotoImage(qr_image)

    # Create a label to hold the image and pack it
    qr_label = tk.Label(qr_window, image=qr_photo)
    qr_label.image = qr_photo  # Keep a reference to avoid garbage collection
    qr_label.pack(pady=20)"""
PAYMONGO_API_KEY = 'sk_test_6zVNpSMrK2VwWCCjqGQyygzt' 
PAYMONGO_API_URL = 'https://api.paymongo.com/v1/links'

def create_gcash_payment_source(amount, description='GCash Payment'):
    encoded_api_key = base64.b64encode(f'{PAYMONGO_API_KEY}:'.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_api_key}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'attributes': {
                'amount': int(amount * 100),  # Convert to centavos
                'currency': 'PHP',
                'description': description,
                'redirect': {
                    'success': 'http://yourdomain.com/success',
                    'failed': 'http://yourdomain.com/failed',
                },
            }
        }
    }

    response = requests.post(PAYMONGO_API_URL, headers=headers, json=data)
    response_data = response.json()

    if response.status_code == 201:
        payment_url = response_data['data']['attributes']['checkout_url']
        return payment_url
    else:
        print(f"Error creating GCash payment: {response_data}")
        return None
 
def generate_gcash_qr(price, new_window):   
    payment_url = "https://pm.link/helloword-ricevendingmachine/test/GtA2ia9"
    if payment_url:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,       
        )
        qr.add_data(payment_url)
        qr.make(fit=True)

        # Create an image from the QR Code instance
        img = qr.make_image(fill="black", back_color="white")

        # Save the image or display it
        img_path = "gcash_payment_qr.png"
        img.save(img_path)

        # Open the QR code in a new window
        show_qr_window(img_path, new_window)
    else:
        print("Failed to create GCash payment.")

def show_qr_window(img_path, new_window):
    # Create a new top-level window
    new_window.withdraw()
    qr_window = tk.Toplevel(root)
    qr_window.configure(bg="#508D4E")
    set_fullscreen(qr_window)
    qr_window.wm_attributes("-type", "override")
    
    closebtn = tk.Button(qr_window, text="Cancel", width=14, height=2, bg="lightgrey", fg="black", font=("Arial", 24,),bd=1, relief="solid",
                            command=lambda: [new_window.deiconify(), qr_window.destroy()])
    closebtn.pack(side=tk.TOP, anchor='nw', padx=20, pady=20)

    # Load the saved QR image
    qr_image = Image.open(img_path)
    qr_photo = ImageTk.PhotoImage(qr_image)

    # Create a label to hold the image and pack it
    qr_label = tk.Label(qr_window, image=qr_photo)
    qr_label.image = qr_photo  # Keep a reference to avoid garbage collection
    qr_label.pack(pady=20)

def fetch_images_from_db(image_ids):
    # Replace with your MySQL connection details
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='password',
        database='RVM'
    )
    
    cursor = connection.cursor()
    
    images = {}
    for image_id in image_ids:
        # Query to fetch the image from the database
        query = "SELECT image FROM rice WHERE id = %s"
        cursor.execute(query, (image_id,))
        image_data = cursor.fetchone()[0]  # Fetch one row and get the first column
        images[image_id] = image_data
    
    cursor.close()
    connection.close()  
    return images

def round_image(image, border_radius):
    # Create a mask to round the corners of the image
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle
    draw.rounded_rectangle(
        (0, 0, image.size[0], image.size[1]),
        radius=border_radius,
        fill=255
    )
    
    # Apply the mask to the image
    rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    rounded_image.putalpha(mask)
    
    # Add border
    border = Image.new('RGBA', image.size, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(
        (0, 0, image.size[0], image.size[1]),
        radius=border_radius,
        outline="black",
        width=10  # Adjust the width and color as needed
    )
    bordered_image = Image.alpha_composite(border, rounded_image)   
    return bordered_image

def display_images(labels, image_ids):
    # Fetch the image data from the database
    images_data = fetch_images_from_db(image_ids)
    
    for label, image_id in zip(labels, image_ids):
        image_data = images_data.get(image_id)
        
        if image_data:
            # Convert the binary data to an image
            image = Image.open(BytesIO(image_data)).convert("RGBA")
            
            # Resize the image to 300x300 pixels
            resized_image = image.resize((590, 400), Image.Resampling.LANCZOS)
            
            # Apply rounded corners and border
            final_image = round_image(resized_image, border_radius=20)  # Adjust the border_radius as needed
            
            # Convert the image to Tkinter format
            tk_image = ImageTk.PhotoImage(final_image)
            
            # Update the label to display the image
            label.config(image=tk_image)
            label.image = tk_image  # Keep a reference to avoid garbage collection
        else:
            print(f"No image data found for image ID {image_id}.")

def set_fullscreen(window):
    # Set fullscreen
    window.attributes("-fullscreen", True)  
    # Get screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Force window geometry to match screen resolution
    window.geometry(f"{screen_width}x{screen_height}")
    
    # Bind Escape key to exit fullscreen
    window.bind("<Escape>", lambda event: window.attributes("-fullscreen", False))

def second_window(event=None):
    root.withdraw()
    main_window = tk.Toplevel(root)
    main_window.configure(bg="#ffffff")
    set_fullscreen(main_window)
    main_window.wm_attributes("-type", "override")

    button_width = 20
    button_height = 5
    button_font = ("Arial", 38)

    # Create a frame for buttons
    button_frame = tk.Frame(main_window, bg="#ffffff")
    button_frame.pack(fill=tk.BOTH, expand=True)

    # Configure rows and columns to expand
    for i in range(3):
        button_frame.columnconfigure(i, weight=1)
        button_frame.rowconfigure(0, weight=1)

    # Create button frames for each column
    button_frame1 = tk.Frame(button_frame, bg="#ffffff", width=550, height=1000, relief="solid", borderwidth=0.5)
    button_frame1.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

    button_frame2 = tk.Frame(button_frame, bg="#ffffff", width=550, height=1000, relief="solid", borderwidth=0.5)
    button_frame2.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

    button_frame3 = tk.Frame(button_frame, bg="#ffffff", width=550, height=1000, relief="solid", borderwidth=0.5)
    button_frame3.grid(row=0, column=2, padx=10, pady=20, sticky="nsew")

    button_frame1.bind("<Button-1>", lambda e: open_home_window(1, button1.cget("text"), label1.cget("text"), main_window))
    button_frame2.bind("<Button-1>", lambda e: open_home_window(2, button2.cget("text"), label2.cget("text"), main_window))
    button_frame3.bind("<Button-1>", lambda e: open_home_window(3, button3.cget("text"), label3.cget("text"), main_window))

    # Create image labels and position them at the top of each button frame
    img1 = tk.Label(button_frame1, bg="#ffffff")  # Placeholder for image
    img1.place(relx=0.5, rely=0.03, anchor="n")  # Position at the top

    img2 = tk.Label(button_frame2, bg="#ffffff")  # Placeholder for image
    img2.place(relx=0.5, rely=0.03, anchor="n")  # Position at the top

    img3 = tk.Label(button_frame3, bg="#ffffff")  # Placeholder for image
    img3.place(relx=0.5, rely=0.03, anchor="n")  # Position at the top

    # Bind click events to each label
    img1.bind("<Button-1>", lambda e: open_home_window(1, button1.cget("text"), label1.cget("text"), main_window))
    img2.bind("<Button-1>", lambda e: open_home_window(2, button2.cget("text"), label2.cget("text"), main_window))
    img3.bind("<Button-1>", lambda e: open_home_window(3, button3.cget("text"), label3.cget("text"), main_window))

    # Create text labels for each image
    global label1
    label1 = tk.Label(button_frame1, text="", font=("Arial", 24, "bold"), fg="black", bg="#ffffff")
    label1.place(relx=0.5, rely=0.6, anchor="center")  # Centered in button_frame1

    global label2
    label2 = tk.Label(button_frame2, text="40 per kg", font=("Arial", 24, "bold"), fg="black", bg="#ffffff")
    label2.place(relx=0.5, rely=0.6, anchor="center")  # Centered in button_frame2

    global label3
    label3 = tk.Label(button_frame3, text="40 per kg", font=("Arial", 24, "bold"), fg="black", bg="#ffffff")
    label3.place(relx=0.5, rely=0.6, anchor="center")  # Centered in button_frame3

    # Create buttons inside the frames, positioned at the bottom of each frame
    global button1
    button1 = tk.Button(button_frame1, text="Select Variety 1", width=button_width, height=button_height,
                        bg="#508D4E", fg="white", font=button_font, command=lambda: open_home_window(1, button1.cget("text"), label1.cget("text"), main_window))
    button1.place(relx=0.5, rely=0.82, anchor="center")  # Position at the bottom of button_frame1

    global button2
    button2 = tk.Button(button_frame2, text="Select Variety 2", width=button_width, height=button_height,
                        bg="#508D4E", fg="white", font=button_font, command=lambda: open_home_window(2, button2.cget("text"), label2.cget("text"), main_window))
    button2.place(relx=0.5, rely=0.82, anchor="center")  # Position at the bottom of button_frame2

    global button3
    button3 = tk.Button(button_frame3, text="Select Variety 3", width=button_width, height=button_height,
                        bg="#508D4E", fg="white", font=button_font, command=lambda: open_home_window(3, button3.cget("text"), label3.cget("text"), main_window))
    button3.place(relx=0.5, rely=0.82, anchor="center")  # Position at the bottom of button_frame3

    button1.bind("<Button-1>", lambda e: open_home_window(1, button1.cget("text"), label1.cget("text"), main_window))
    button2.bind("<Button-1>", lambda e: open_home_window(2, button2.cget("text"), label2.cget("text"), main_window))
    button3.bind("<Button-1>", lambda e: open_home_window(3, button3.cget("text"), label3.cget("text"), main_window))

    fetch_data_and_display()
    display_images([img1, img2, img3], [1, 2, 3])

# Create the main window
root = tk.Tk()
root.configure(background="#F5F5F5")
set_fullscreen(root)
root.wm_attributes("-type", "override")
root.wm_title("")  # This line is already in your code, but it's not working because you're setting the window to full screen
gif = AnimatedGIF(root, "/home/heartryan/my_raspberry_pi_project/1022(7).gif", 
                           width=820, height=620,interval=100)
gif.bind_click(second_window)
# Create some windows
root.mainloop()







































