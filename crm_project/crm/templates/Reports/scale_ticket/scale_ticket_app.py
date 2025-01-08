import tkinter as tk
from tkinter import messagebox, ttk
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tkinter import filedialog
from datetime import *
import os
import random
from reportlab.lib.colors import Color
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
import csv

reports_folder = os.path.join(os.getcwd(), 'reports')
if not os.path.exists(reports_folder):
    os.makedirs(reports_folder)

# Path to logo
logo_path = os.path.join(os.path.dirname(__file__), 'pictures','logo.png')

# Predefined materials with price per kg
materials_list = {
    'Baled Cardboard': 0.05,
    'Flexible Plastic': 0.2,
    'Mixed Container': 0.03,
    'Pallets': 0.0,
    'Kraft Paper Bags': 0.04,
    'Loose Cardboard': 0.04,
    'Cardboard in Loose': 0.03,

}

# Predefined customers
customers = [
    "Meridian Farm Market Ralphs,19168 39th Ave Unit 114,Surrey BC",
    "Zenpack Canada Inc.,8685 Armstrong Ave,Burnaby BC V3N 2H4",
    "T-BROTHERS - 120-1658 Industrial Ave,Port Coquitlam BC V3C 6N3 ",
    "Customer 4 - adress"
]

# license plate number
plate_number = [
    'SY1341',
    'WB3291',
    '153'
]
# Store materials for the ticket
materials = []
ticket_num = []

# Function to create PDF
def generate_pdf(ticket_number, date, time_in, time_out, customers_lines, materials, file_path, licence, gross, tare,
                 net, pallets):
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    total = 0

    # Font and color for the company name
    company_name_font = "Helvetica-Bold"
    company_name_size = 14
    company_name_color = Color(0.1, 0.3, 0.6)  # Light blue color

    # Add logo
    try:
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"No logo found at: {logo_path}")
        c.drawImage(logo_path, 80, height - 70, width=40, height=40)
    except Exception as e:
        messagebox.showwarning('Error', str(e))

    # Add company name with custom font and color
    c.setFont(company_name_font, company_name_size)
    c.setFillColor(company_name_color)
    c.drawString(130, height - 45, "Local to Global Recycling Inc.")

    # Add remaining details in default font and color
    c.setFont("Helvetica", 8)
    c.setFillColor(Color(0, 0, 0))  # Black color
    c.drawString(130, height - 55, "19090 Lougheed Hwy.")
    c.drawString(130, height - 65, "Pitt Meadows, BC V3Y 2M6")
    c.drawString(80, height - 84, "-" * 80)
    c.drawString(80, height - 110, f"Ticket #: {ticket_number}")
    c.drawString(80, height - 130, f"Date: {date}")
    c.drawString(80, height - 150, f'Time in: {time_in} - Time out: {time_out}')
    c.drawString(80, height - 180, 'Customer:')

    # Customer details with line breaks
    y_position = height - 200
    for line in customers_lines:
        c.drawString(85, y_position, line.strip())
        y_position -= 15

    # Licence and weights
    c.drawString(400, height - 110, f"Licence: {licence}")
    c.drawString(400, height - 130, f"Gross: {gross}")
    c.drawString(400, height - 150, f"Tare: {tare}")
    c.drawString(400, height - 170, f"Net: {net}")
    c.drawString(400, height - 190, f"Pallets #: {pallets}")


    #table headlight
    table_data = [['MATERIAL', 'WEIGHT (KG)', 'PRICE ($/KG)', 'AMOUNT']]

    #add materials in the table
    for material in materials:
        material_type, weight_net, price_per_ton = material
        if material_type == 'Pallets':
            amount = 0
            table_data.append([material_type, f'{weight_net}'])
        else:
            amount = weight_net * price_per_ton
            total += amount
            table_data.append([material_type, f"{weight_net}", f'{price_per_ton}', f"{amount:.2f}"])

    # Table stile creaction
    table = Table(table_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',(0,0),(-1,-1), 8), # set front size
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica',8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))

    # Display table
    y_position -= 60  # lower customer table
    table.wrapOn(c, width, height)
    table.drawOn(c, 80, y_position)


    # Display total amount at the end
    c.drawString(80, y_position - 20, f"Total: ${total:.2f}")
    c.save()
    messagebox.showinfo("Success", "PDF saved successfully!")

# Function to add material
def add_material():
    material_type = material_combobox.get()
    try:
        weight_net = float(weight_entry.get())
        price_per_ton = materials_list[material_type]  # Get price from predefined materials
        materials.append((material_type, weight_net, price_per_ton))

        # Update materials listbox
        if material_type == 'Pallets':
            materials_listbox.insert(tk.END, f"{material_type}: {weight_net} kg")  # Display only weight for pallets
        else:
            materials_listbox.insert(tk.END, f"{material_type}: {weight_net} kg at ${price_per_ton:.2f}/kg")

        messagebox.showinfo("Success", "Material added!")
        weight_entry.delete(0, tk.END)
    except ValueError:
        messagebox.showwarning("Input Error", "Please enter valid numeric weights.")

# Function to save PDF
def save_pdf():
    ticket_number = entry_ticket_number.get()
    date = entry_date.get()
    time_in = entry_time_in.get()
    time_out = entry_time_out.get()
    customer_name = customer_combobox.get()
    licence = licence_entry.get()
    gross = gross_weight_entry.get()
    tare = tare_weight_entry.get()
    net = net_weight_entry.get()
    pallets = pallets_entry.get()

    # Split customer name into multiple lines based on comma
    customers_lines = customer_name.split(',')

    # Вычисление общего веса и налога
    total = sum(m[1] * m[2] for m in materials if m[0] != 'Pallets')
    GST = total * 0.05  # 5% TAX

    # Open dialog to choose save location
    file_name = f"scale_ticket_{ticket_number}_{customer_name.replace(' ', '_').replace(',', '').lower()}.pdf"
    file_path = os.path.join(reports_folder, file_name)  # Save in reports folder

    if file_path:
        generate_pdf(ticket_number, date, time_in, time_out, customers_lines, materials, file_path, licence, gross,
                     tare, net, pallets)

        # Передаем GST и total в функцию save_ticket_info_to_csv
        save_ticket_info_to_csv(ticket_number, date, customer_name, materials, licence, net, GST, total)



# Function to generate a new ticket number
def generate_ticket_number():
    try:
        # Reading last number
        if os.path.exists("last_ticket_number.txt"):
            with open("last_ticket_number.txt", "r") as file:
                current_number = int(file.read().strip())
        else:
            current_number = 103484

        random_increment = random.randint(10, 20)
        new_ticket_number = current_number + random_increment
        entry_ticket_number.delete(0, tk.END)
        entry_ticket_number.insert(0, str(new_ticket_number))

        # Saving new number
        with open("last_ticket_number.txt", "w") as file:
            file.write(str(new_ticket_number))

    except ValueError:
        messagebox.showwarning("Input Error", "Please enter a valid ticket number.")

# Function to calculate net weight
def calculate_net_weight():
    try:
        gross = gross_weight_entry.get()
        tare = tare_weight_entry.get()

        # empty string check
        if gross == "" or tare == "":
            return

        gross = float(gross)
        tare = float(tare)
        net = gross - tare

        # clearing and adding new value
        net_weight_entry.delete(0, tk.END)
        net_weight_entry.insert(0, str(net))
    except ValueError:
        pass


# Function to save ticket information to CSV
def save_ticket_info_to_csv(ticket_number, date, customer_name, materials, licence, net, GST, total):
    csv_file_name = f"scale_ticket_{ticket_number}_{customer_name.replace(' ', '_').replace(',', '').lower()}.csv"
    csv_file_path = os.path.join(reports_folder, csv_file_name)  # Save in reports folder

    header = ['Date', 'Customer', 'Material Info', 'Ticket #', 'Licence', 'Net Weight', 'GST', 'Total']

    # Check if the file exists to write the header
    file_exists = os.path.isfile(csv_file_path)

    # Open the file to append
    with open(csv_file_path,  mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write the header if the file doesn't exist
        if not file_exists:
            writer.writerow(header)

        # Convert materials to a string
        material_info = ', '.join([f"{m[0]}: {m[1]} kg at ${m[2]:.2f}/kg" for m in materials])

        # Write the ticket data
        writer.writerow([date, customer_name, material_info, ticket_number, licence, net, f"{GST:.2f}", f"{total:.2f}"])


# Create main mmenu
root = tk.Tk()
root.title("Scale Ticket Generator")
root.geometry("500x900")

def edit_materials():
    try:
        # Get the selected material from the list
        selected_index = materials_listbox.curselection()[0]
        selected_material = materials[selected_index]

        # Extract material details
        materials_type, weight_net, price_per_ton = selected_material

        # Ask user for new weight
        net_weight = float(weight_entry.get())

        # Update the material with the new weight
        materials[selected_index] = (materials_type, net_weight, price_per_ton)

        # Update the listbox
        materials_listbox.delete(selected_index)
        if materials_type == 'Pallets':
            materials_listbox.insert(selected_index, f'{materials_type}: {net_weight} kg')
        else:
            materials_listbox.insert(selected_index, f"{materials_type}: {net_weight} kg at ${price_per_ton:.2f}/kg")

        messagebox.showinfo('Materials updated!')
        weight_entry.delete(0, tk.END)  # Clear the weight entry field

    except IndexError:
        messagebox.showwarning('Selection Error', 'Please select a material to edit.')
    except ValueError:
        messagebox.showwarning('Input Error', 'Please enter a valid weight.')


def generate_time_out(time_in):
    try:

        time_in_obj = datetime.strptime(time_in, '%H:%M')
        ran_min = random.randint(10,20)
        time_out_obj = time_in_obj + timedelta(minutes=ran_min)
        return time_out_obj.strftime('%H:%M')
    except ValueError:
        return ''

def update_time_out():
    time_in = entry_time_in.get()
    try:
        if time_in:
            time_out = generate_time_out(time_in)
            entry_time_out.delete(0, tk.END)
            entry_time_out.insert(0,time_out)
    except ValueError:
        pass

# Add the "Edit material" button
edit_materials_button = tk.Button(root, text="Edit material", command=edit_materials)
edit_materials_button.pack(pady=5)




# Input fields
tk.Label(root, text="Ticket #:").pack()
entry_ticket_number = tk.Entry(root)
entry_ticket_number.pack()

tk.Button(root, text="Generate Ticket Number", command=generate_ticket_number).pack(pady=5)

tk.Label(root, text="Date (YYYY-MM-DD):").pack()
entry_date = tk.Entry(root)
entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
entry_date.pack()

tk.Label(root, text="Time in (HH:MM):").pack()
entry_time_in = tk.Entry(root)
entry_time_in.insert(0, datetime.now().strftime("%H:%M"))
entry_time_in.pack()

entry_time_in.bind("<KeyRelease>", lambda e: update_time_out())


tk.Label(root, text="Time out (HH:MM):").pack()
entry_time_out = tk.Entry(root)
entry_time_out.insert(0, datetime.now().strftime("%H:%M"))
entry_time_out.pack()

tk.Label(root, text="Customer:").pack()
customer_combobox = ttk.Combobox(root, values=customers)
customer_combobox.pack()

tk.Label(root, text="Licence:").pack()
licence_entry = ttk.Combobox(root, values=plate_number)
licence_entry.pack()
licence_entry.set(plate_number[0])

tk.Label(root, text="Gross Weight (kg):").pack()
gross_weight_entry = tk.Entry(root)
gross_weight_entry.pack()

tk.Label(root, text="Tare Weight (kg):").pack()
tare_weight_entry = tk.Entry(root)
tare_weight_entry.pack()

tk.Label(root, text="Net Weight (kg):").pack()
net_weight_entry = tk.Entry(root)
net_weight_entry.pack()

# Automatically update net weight
gross_weight_entry.bind("<KeyRelease>", lambda e: calculate_net_weight())
tare_weight_entry.bind("<KeyRelease>", lambda e: calculate_net_weight())

# Material selection and input
tk.Label(root, text="Material:").pack()
material_combobox = ttk.Combobox(root, values=list(materials_list.keys()))
material_combobox.pack()

tk.Label(root, text="Weight (kg):").pack()
weight_entry = tk.Entry(root)
weight_entry.pack()

tk.Button(root, text="Add Material", command=add_material).pack(pady=5)

materials_listbox = tk.Listbox(root)
materials_listbox.pack()

tk.Label(root, text="Pallets #:").pack()
pallets_entry = tk.Entry(root)
pallets_entry.pack()

tk.Button(root, text="Save PDF", command=save_pdf).pack(pady=10)

# Run the main loop
root.mainloop()

reports_folder = os.path.join(os.getcwd(), 'reports')
if not os.path.exists(reports_folder):
    os.makedirs(reports_folder)