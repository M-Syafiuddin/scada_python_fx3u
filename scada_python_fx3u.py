"""
--------------------------------------------------------------------------
#import modul yang dibutuhkan

pada tahap ini kita akan mengimport modul yang
dibutuhkan dengan cara tertentu
______________________________________________'
"""
#kita mengimport modul tkinter sebagai tk
#agar saat kita memanggil objek kita tidak
#memangil "tkinter" melainkan hanya "tk"
import tkinter as tk
#kita mengimport class massagebox
#di modul tkinter
from tkinter import messagebox
#kita mengimport class ModbusTcpClient
#dimodul pymodbus lalu ke folder client 
#lalu ke folder sync
from pymodbus.client.sync import ModbusTcpClient

"""
---------------------------------------------------------------------------------
#buat class ScadaPLCApp()

pada tahap ini kita akan buat class ScadaPLCApp
yang merasi class tk.Tk, class ini isinya menuta
---------------------------------------------------------------------------------
"""
class ScadaPLCApp(tk.Tk):
    #membuat konstruktor
    def __init__(self):
        #memanggil konstruktor dari class induk
        super().__init__()
        #tetapkan spesifikasi window
        self.title("SCADA MINI: MULTI-PAGE MONITORING")
        self.geometry("500x700")
        
        #tetapkan Parameter PLC
        self.plc_ip = '192.168.0.7'
        self.plc_port = 502
        self.slave_id = 1
        
        # tetapkan Terminal Digital Plc
        self.output_range = range(6)
        self.input_range = range(8)
        
        # Container utama untuk menumpuk frame
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        #mendeklarasikan dictionary untuk wadah 
        #beberapa objek frame
        self.frames = {}

        # Membuat kedua halaman
        for F in (DigitalPage, AnalogPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

       # Menampilkan frame saat  pertama class ini dijalankan
         self.show_frame("DigitalPage")
        
        # Jalankan loop monitoring
        self.update_data_loop()

    #metode untuk menampilkan frame saat pertama class
    #ini dijalankan
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    #metode untuk menjalankan loop monitoring digital input 
    #pada saat frame DigitalPage tampil atau monitoring analog output
    #pada saat frame AnalogPage tampil
    def update_data_loop(self):
        """Loop tunggal untuk memperbarui data di halaman yang aktif"""
        client = ModbusTcpClient(self.plc_ip, port=self.plc_port)
        try:
            if client.connect():
                # Update Digital (X)
                res_x = client.read_discrete_inputs(0, count=8, unit=self.slave_id)
                if not res_x.isError():
                    self.frames["DigitalPage"].update_inputs(res_x.bits)

                # Update Analog (Contoh membaca D0-D3)
                # FC03: Read Holding Registers
                res_a = client.read_holding_registers(0, count=4, unit=self.slave_id)
                if not res_a.isError():
                    self.frames["AnalogPage"].update_analogs(res_a.registers)
        except Exception as e:
            print(f"Polling Error: {e}")
        finally:
            client.close()
            self.after(1000, self.update_data_loop)

# --- HALAMAN DIGITAL (X & Y) ---
class DigitalPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="DIGITAL I/O CONTROL", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Tombol Navigasi
        tk.Button(self, text="Ke Halaman Analog >>", command=lambda: controller.show_frame("AnalogPage")).pack()

        # UI Input X
        self.input_lamps = []
        input_frame = tk.LabelFrame(self, text=" INPUT MONITOR (X) ", padx=10, pady=10)
        input_frame.pack(padx=20, pady=10, fill="x")
        
        for i in range(8):
            row = tk.Frame(input_frame); row.pack(side="left", padx=5)
            cvs = tk.Canvas(row, width=25, height=25, highlightthickness=0); cvs.pack()
            lamp = cvs.create_oval(5, 5, 20, 20, fill="#1a5e20")
            tk.Label(row, text=f"X{i}").pack()
            self.input_lamps.append((cvs, lamp))

        # UI Output Y
        self.output_lamps = []
        output_frame = tk.LabelFrame(self, text=" CONTROL OUTPUT (Y) ", padx=10, pady=10)
        output_frame.pack(padx=20, pady=10, fill="both")

        for i in range(6):
            row = tk.Frame(output_frame, pady=5); row.pack(fill="x")
            tk.Label(row, text=f"Output Y{i}", width=10).pack(side="left")
            cvs = tk.Canvas(row, width=25, height=25, highlightthickness=0); cvs.pack(side="left", padx=10)
            lamp = cvs.create_oval(5, 5, 20, 20, fill="gray")
            self.output_lamps.append((cvs, lamp))
            
            tk.Button(row, text="ON", bg="#2ecc71", command=lambda a=i: self.write_y(a, True)).pack(side="left", padx=2)
            tk.Button(row, text="OFF", bg="#e74c3c", command=lambda a=i: self.write_y(a, False)).pack(side="left", padx=2)

    def update_inputs(self, bits):
        for i in range(8):
            color = "#00ff00" if bits[i] else "#1a5e20"
            self.input_lamps[i][0].itemconfig(self.input_lamps[i][1], fill=color)

    def write_y(self, addr, status):
        client = ModbusTcpClient(self.controller.plc_ip, port=self.controller.plc_port)
        if client.connect():
            res = client.write_coil(addr, status, unit=self.controller.slave_id)
            if not res.isError():
                color = "yellow" if status else "gray"
                self.output_lamps[addr][0].itemconfig(self.output_lamps[addr][1], fill=color)
            client.close()

# --- HALAMAN ANALOG (Registers) ---
class AnalogPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="ANALOG I/O MONITOR", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Tombol Navigasi
        tk.Button(self, text="<< Ke Halaman Digital", command=lambda: controller.show_frame("DigitalPage")).pack()

        # UI Analog Input (Contoh Read Register D0-D3)
        self.analog_labels = []
        ai_frame = tk.LabelFrame(self, text=" ANALOG INPUT (D0 - D3) ", padx=10, pady=10)
        ai_frame.pack(padx=20, pady=10, fill="x")

        for i in range(4):
            row = tk.Frame(ai_frame, pady=5); row.pack(fill="x")
            tk.Label(row, text=f"Register D{i}: ", font=("Arial", 10)).pack(side="left")
            val_label = tk.Label(row, text="0", font=("Arial", 10, "bold"), fg="blue")
            val_label.pack(side="left")
            self.analog_labels.append(val_label)

        # UI Analog Output (Contoh Write Register D10)
        ao_frame = tk.LabelFrame(self, text=" ANALOG OUTPUT CONTROL (D10) ", padx=10, pady=10)
        ao_frame.pack(padx=20, pady=10, fill="x")
        
        self.ao_value = tk.IntVar(value=0)
        tk.Scale(ao_frame, from_=0, to=4000, orient="horizontal", variable=self.ao_value).pack(fill="x", padx=10)
        tk.Button(ao_frame, text="Write to D10", command=self.write_analog).pack(pady=5)

    def update_analogs(self, values):
        for i in range(len(values)):
            if i < len(self.analog_labels):
                self.analog_labels[i].config(text=str(values[i]))

    def write_analog(self):
        val = self.ao_value.get()
        client = ModbusTcpClient(self.controller.plc_ip, port=self.controller.plc_port)
        if client.connect():
            # Menulis ke register D10 (alamat 10)
            res = client.write_register(10, val, unit=self.controller.slave_id)
            if res.isError():
                messagebox.showerror("Error", "Gagal menulis data analog")
            client.close()

if __name__ == "__main__":
    app = ScadaPLCApp()
    app.mainloop()

